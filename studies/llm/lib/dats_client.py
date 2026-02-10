import json
import time
from typing import Any, Callable
import requests

from .pdf import make_pdf


class DatsClient:
    def __init__(self, base_url: str, username: str, password: str, timeout: float):
        self.base_url = str(base_url).rstrip("/")
        self.username = username
        self.password = password
        self.timeout = float(timeout)

        self.session = requests.Session()
        self._token = self._authenticate()

    def _url(self, path: str) -> str:
        return f"{self.base_url}{"/" + path if not path.startswith("/") else path}"

    def _authenticate(self) -> str:
        return self.post("/authentication/login",
                         data={"username": self.username,
                               "password": self.password}
                         ).get("access_token")

    def request(self, method: str, path: str, **kwargs) -> Any:
        r = self.session.request(method,
                                 self._url(path),
                                 headers={
                                     **kwargs.pop("headers", {}),
                                     "Authorization": f"Bearer {self._token}" if hasattr(self, "_token") else "",
                                 },
                                 timeout=self.timeout,
                                 **kwargs)

        if r.status_code == 401:
            self._token = self._authenticate()
            return self.request(method, path, **kwargs)
        elif r.status_code == 404:
            return None
        r.raise_for_status()

        return {} if not r.content else r.json()

    def get(self, path: str) -> Any:
        return self.request("GET", path)

    def post(self, path: str, json=None, data=None, files=None) -> Any:
        return self.request("POST", path, json=json, data=data, files=files)

    def put(self, path: str, json=None, data=None, files=None) -> Any:
        return self.request("PUT", path, json=json, data=data, files=files)

    def patch(self, path: str, json=None) -> Any:
        return self.request("PATCH", path, json=json)

    def delete(self, path: str) -> Any:
        return self.request("DELETE", path)

    def poll(self,
             fn: Callable[[], Any],
             is_ready: Callable[[Any], bool],
             poll_interval=5.0) -> Any:
        t0 = time.time()
        while True:
            result = fn()
            if is_ready(result):
                return result

            if time.time() - t0 > self.timeout:
                raise TimeoutError("Polling timed out")
            time.sleep(poll_interval)

    def ensure_project(self, title: str, description: str = "Vigil LLM case study project", recreate: bool = False) -> int:
        for project in self.get("/project/user/projects") or []:
            if str(project.get("title")) == title:
                if recreate:
                    self.delete(f"/project/{project['id']}")
                else:
                    return int(project["id"])

        id = self.put(
            "/project", json={"title": title, "description": description})["id"]
        if id is None:
            raise RuntimeError("Failed to create project.")
        return int(id)

    def ensure_document(self, proj_id: int, seed_language: str, seed_text: str) -> int:
        filename = "vigil-seed.pdf"

        sdoc_id = self.get(
            f"/project/{proj_id}/resolve_filename/{filename}")

        if sdoc_id is None:
            self.put(f"/docprocessing/project/{proj_id}", files=[
                ("uploaded_files",
                 (filename, make_pdf(seed_text), "application/pdf"))
            ], data={"settings": json.dumps({
                "language": seed_language,
                "extract_images": False,
                "pages_per_chunk": 1,
                "keyword_number": 5,
                "keyword_deduplication_threshold": 0.5,
                "keyword_max_ngram_size": 2
            })})

            sdoc_id = self.poll(
                lambda: self.get(
                    f"/project/{proj_id}/resolve_filename/{filename}"),
                is_ready=lambda x: x is not None,
            )
        else:
            self.patch(f"/sdoc/{sdoc_id}", json={
                "settings": {
                    "language": seed_language,
                    "extract_images": False,
                    "pages_per_chunk": 1,
                    "keyword_number": 5,
                    "keyword_deduplication_threshold": 0.5,
                    "keyword_max_ngram_size": 2
                }
            })

        meta = self.get(f"/sdocmeta/sdoc/{sdoc_id}/metadata/language")
        if isinstance(meta, dict) and "id" in meta:
            self.delete(f"/sdocmeta/{meta['id']}")
        self.put("/sdocmeta", json={
            "source_document_id": sdoc_id,
            "project_metadata_id": self.ensure_metadata(proj_id=proj_id, keys=["language"])[0],
            "str_value": seed_language,
            "int_value": None,
            "boolean_value": None,
            "date_value": None,
            "list_value": None,
        })

        return sdoc_id

    def ensure_metadata(
        self,
        proj_id: int,
        keys: list[str],
        descriptions: dict[str, str] | None = None,
        update_existing: bool = False,
    ) -> list[int]:
        descriptions = descriptions or {}
        wanted = list(keys)  # do not mutate caller list
        meta_ids: list[int] = []

        existing = self.get(f"/projmeta/project/{proj_id}") or []
        by_key = {str(m.get("key"))                  : m for m in existing if m.get("id") is not None}

        for key in wanted:
            if key in by_key:
                m = by_key[key]
                meta_ids.append(int(m["id"]))

                if update_existing:
                    desired_desc = descriptions.get(key)
                    if desired_desc is not None and str(m.get("description")) != desired_desc:
                        self.patch(
                            f"/projmeta/{m['id']}", json={"description": desired_desc})
            else:
                meta_ids.append(int(self.put("/projmeta", json={
                    "key": key,
                    "metatype": "STRING",
                    "doctype": "text",
                    "description": descriptions.get(key, "vigil seed metadata"),
                    "project_id": proj_id,
                    "read_only": False,
                })["id"]))

        return meta_ids

    def ensure_codes(
        self,
        proj_id: int,
        codes: list[str],
        descriptions: dict[str, str] | None = None,
        update_existing: bool = False,
    ) -> list[int]:
        descriptions = descriptions or {}
        wanted = list(codes)
        code_ids: list[int] = []

        existing = self.get(f"/code/project/{proj_id}") or []
        by_name = {str(c.get("name"))
                       : c for c in existing if c.get("id") is not None}

        for name in wanted:
            if name in by_name:
                c = by_name[name]
                code_ids.append(int(c["id"]))

                if update_existing:
                    desired_desc = descriptions.get(name)
                    if desired_desc is not None and str(c.get("description")) != desired_desc:
                        self.patch(f"/code/{c['id']}",
                                   json={"description": desired_desc})
            else:
                code_ids.append(int(self.put("/code", json={
                    "project_id": proj_id,
                    "name": name,
                    "description": descriptions.get(name, "vigil seed code"),
                    "is_system": False,
                })["id"]))

        return code_ids

    def ensure_tags(self, proj_id: int, tags: list[str]) -> list[int]:
        tag_ids = []

        for tag in self.get(f"/tag/project/{proj_id}") or []:
            if str(tag.get("name")) in tags and tag.get("id") is not None:
                tag_ids.append(int(tag["id"]))
                tags.remove(str(tag.get("name")))

        for tag in tags:
            tag_ids.append(int(self.put("/tag", json={
                "project_id": proj_id,
                "name": tag,
                "description": "vigil seed tag",
                "is_system": False}
            )["id"]))

        return tag_ids
