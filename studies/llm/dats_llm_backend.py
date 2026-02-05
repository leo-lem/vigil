from __future__ import annotations

from core import Backend
from studies.llm.lib.dats_client import DatsClient


class DatsLlm(Backend):
    def __init__(
        self,
        username: str,
        password: str,
        project_name: str,
        base_url: str = "https://dats.ltdemos.informatik.uni-hamburg.de/api",
        timeout_s: float = 30.0,
        recreate_project: bool = False,
    ):
        self._client = DatsClient(
            base_url=base_url,
            username=username,
            password=password,
            timeout=timeout_s,
        )

        self.supported_job_types = {
            "SENTENCE_ANNOTATION",
            "TAGGING",
            "METADATA_EXTRACTION",
        }
        self.supported_approach_types = {
            "LLM_ZERO_SHOT",
            "LLM_FEW_SHOT",
        }
        self.supported_languages = {"en", "de"}

        environment = {
            "project_name": project_name,
            "recreate_project": recreate_project,
        }

        function = {
            "llm_job_type": "SENTENCE_ANNOTATION",
            "llm_approach_type": "LLM_ZERO_SHOT",
            "codes": ["Positive", "Negative", "Neutral"],
        }

        super().__init__(environment=environment, function=function)

    def update_environment(self, environment: dict) -> None:
        self.environment["project_id"] = self._client.ensure_project(
            environment["project_name"],
            recreate=environment["recreate_project"],
        )

    def compute(self, input: dict, function: dict):
        if "text" not in input:
            raise KeyError("input must include 'text'")

        language = input.get("language", "en")
        if language not in self.supported_languages:
            raise ValueError(
                f"language must be one of {sorted(self.supported_languages)}")

        document_id = self._client.ensure_document(
            self.environment["project_id"],
            language,
            input["text"],
        )

        job_type = function.get("llm_job_type")
        approach = function.get("llm_approach_type")

        if job_type not in self.supported_job_types:
            raise KeyError(
                f"llm_job_type must be one of {sorted(self.supported_job_types)}")
        if approach not in self.supported_approach_types:
            raise KeyError(
                f"llm_approach_type must be one of {sorted(self.supported_approach_types)}")
        if job_type in {"TAGGING", "METADATA_EXTRACTION"} and approach == "LLM_FEW_SHOT":
            raise ValueError(f"{job_type} does not support LLM_FEW_SHOT")

        payload = dict(input)
        payload.update(function)
        payload["project_id"] = self.environment["project_id"]

        stp = payload.setdefault("specific_task_parameters", {})
        stp["llm_job_type"] = job_type
        stp["sdoc_ids"] = [document_id]

        sap = payload.setdefault("specific_approach_parameters", {})
        sap["llm_approach_type"] = approach

        if job_type == "SENTENCE_ANNOTATION":
            codes = function.get("codes")
            if not codes:
                raise KeyError(
                    "codes must be provided for SENTENCE_ANNOTATION")
            stp["code_ids"] = self._client.ensure_codes(
                payload["project_id"],
                codes,
            )

        elif job_type == "TAGGING":
            tags = function.get("tags")
            if not tags:
                raise KeyError("tags must be provided for TAGGING")
            stp["tag_ids"] = self._client.ensure_tags(
                payload["project_id"],
                tags,
            )

        elif job_type == "METADATA_EXTRACTION":
            keys = function.get("metadata_keys")
            if not keys:
                raise KeyError(
                    "metadata_keys must be provided for METADATA_EXTRACTION")
            stp["project_metadata_ids"] = self._client.ensure_metadata(
                payload["project_id"],
                keys,
            )

        if "prompts" not in sap:
            if approach == "LLM_ZERO_SHOT":
                sap["prompts"] = self._client.post(
                    f"/llm/create_prompt_templates?approach_type={approach}",
                    json={
                        "llm_job_params": {
                            "project_id": payload["project_id"],
                            "llm_job_type": job_type,
                            "specific_task_parameters": stp,
                        }
                    },
                )
            else:
                raise NotImplementedError(
                    "LLM_FEW_SHOT prompt generation not supported")

        job_id = self._client.post(
            "/llm/llm_assistant",
            json=payload,
        ).get("job_id")

        if not job_id:
            raise RuntimeError("failed to create LLM job")

        job = self._client.poll(
            lambda: self._client.get(f"/llm/llm_assistant/{job_id}"),
            is_ready=lambda x: x.get("status") in {
                "finished",
                "failed",
                "aborted",
                "done",
                "completed",
                "success",
                "error",
                "cancelled",
            },
        )

        return self._clean_result(job)

    def _clean_result(self, job: dict) -> dict:
        out = dict(job)
        for k in ("job_id", "created", "finished"):
            out.pop(k, None)

        try:
            anns = (
                out["output"]
                ["specific_task_result"]
                ["results"][0]
                ["suggested_annotations"]
            )

            codes = self._client.get(
                f"/code/project/{self.environment['project_id']}") or []

            for ann in anns:
                for k in ("id", "created", "updated"):
                    ann.pop(k, None)
                ann["code_name"] = next(
                    (c["name"]
                     for c in codes if c.get("id") == ann.get("code_id")),
                    None,
                )
        except Exception:
            pass  # ignore errors in cleaning annotations

        return out
