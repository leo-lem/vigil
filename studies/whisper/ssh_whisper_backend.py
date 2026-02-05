from __future__ import annotations

from requests import post

from core import Backend
from studies.whisper.lib.tunnel_ssh import tunnel_ssh


class SshWhisper(Backend):
    def __init__(
        self,
        host: str,
        ssh_user: str,
        remote_port: int = 10130,
        local_port: int = 10130,
        jump_host: str | None = None,
        endpoint: str = "/whisper/transcribe",
        content_type: str = "application/octet-stream",
        language: str | None = None,
        timeout_s: float = 120.0,
    ):
        self._ssh_user = ssh_user
        self._jump_host = jump_host
        self._remote_port = int(remote_port)
        self._local_port = int(local_port)
        self._timeout_s = float(timeout_s)

        self._endpoint = endpoint
        self._content_type = content_type
        self._language = language

        self._host = host
        self._tunnel = tunnel_ssh(
            ssh_user=ssh_user,
            remote_host=host,
            remote_port=self._remote_port,
            local_port=self._local_port,
            jump_host=jump_host,
        )

        super().__init__(
            environment={"host": host, "port": self._remote_port},
            function={
                "endpoint": endpoint,
                "content_type": content_type,
                "language": language,
            },
        )

    def update_environment(self, environment: dict) -> None:
        host = environment.get("host", self._host)
        port = int(environment.get("port", self._remote_port))

        if host == self._host and port == self._remote_port:
            return

        self._host = host
        self._remote_port = port

        self._tunnel.terminate()
        self._tunnel = tunnel_ssh(
            ssh_user=self._ssh_user,
            remote_host=host,
            remote_port=port,
            local_port=self._local_port,
            jump_host=self._jump_host,
        )

        self.environment = {"host": host, "port": port}

    def compute(self, input: str | dict, function: dict) -> dict:
        endpoint = function.get("endpoint", self._endpoint)
        base_url = f"http://127.0.0.1:{self._local_port}{endpoint}"

        language = function.get("language", self._language)
        headers = {
            "Content-Type": function.get("content_type", self._content_type)}
        params = {"language": language} if language else {}

        chunk_s = None
        overlap_s = None

        if isinstance(input, str):
            source_data = input
            parts = [{"data": input, "start_ms": 0}]
        elif isinstance(input, dict):
            source_data = input.get("data")
            parts = input.get("parts")
            if parts is None:
                parts = [{"data": source_data, "start_ms": 0}]
            chunk_s = input.get("chunk_s")
            overlap_s = input.get("overlap_s")
        else:
            raise TypeError("backend input must be str (path) or dict")

        all_segments: list[dict] = []
        transcript: list[str] = []
        lang: str | None = None
        lang_probs: list[float] = []

        for part in parts:
            audio_path = part["data"]
            offset_ms = int(part.get("start_ms", 0))

            with open(audio_path, "rb") as f:
                resp = post(
                    base_url,
                    params=params,
                    headers=headers,
                    data=f.read(),
                    timeout=self._timeout_s,
                )
            resp.raise_for_status()
            payload = resp.json()

            if lang is None:
                lang = payload.get("language")

            lp = payload.get("language_probability")
            if lp is not None:
                lang_probs.append(float(lp))

            for seg in payload.get("segments", []) or []:
                if "start_ms" in seg:
                    seg["start_ms"] += offset_ms
                if "end_ms" in seg:
                    seg["end_ms"] += offset_ms

                for w in seg.get("words", []) or []:
                    if "start_ms" in w:
                        w["start_ms"] += offset_ms
                    if "end_ms" in w:
                        w["end_ms"] += offset_ms
                    t = w.get("text")
                    if isinstance(t, str):
                        t = t.strip()
                        if t:
                            transcript.append(t)

                all_segments.append(seg)

        out = {
            "segments": all_segments,
            "transcript": " ".join(transcript),
            "language": lang if lang is not None else language,
            "language_probability": max(lang_probs) if lang_probs else None,
            "num_parts": len(parts),
            "source_data": source_data,
        }

        if chunk_s is not None:
            out["chunk_s"] = chunk_s
        if overlap_s is not None:
            out["overlap_s"] = overlap_s

        return out
