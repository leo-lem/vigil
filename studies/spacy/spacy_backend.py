from __future__ import annotations

from typing import Any

import os
import spacy
import spacy.cli

from core import Backend


class Spacy(Backend):
    """
    Local spaCy backend.

    Parameters
    ----------
    model:
        spaCy model name or path.

    disable:
        Pipeline components disabled at load time.
    """

    def __init__(self, model: str = "en_core_web_sm", disable: list[str] | None = None):
        self._nlp_cache: dict[Spacy.ModelKey, Any] = {}

        function = {
            "model": model,
            "disable": list(disable or []),
        }

        super().__init__(environment={}, function=function)

    def update_environment(self, environment: dict[str, Any]) -> None:
        return None

    def compute(self, input: dict[str, Any], function: dict[str, Any]) -> dict[str, Any]:
        text = input.get("text")
        if not isinstance(text, str):
            raise KeyError("input must include 'text'")

        model = function.get("model")
        disable = tuple(function.get("disable", []))

        nlp = self._grab_nlp(model=model, disable=disable)
        doc = nlp(text)

        out: dict[str, Any] = {
            "text": text,
            "model": model,
            "disabled": list(disable),
            "pipeline": list(getattr(nlp, "pipe_names", [])),
            "tokens": [
                {
                    "i": int(t.i),
                    "text": t.text,
                    "idx": int(t.idx),
                    "start_char": int(t.idx),
                    "end_char": int(t.idx + len(t.text)),
                    "lemma": t.lemma_,
                    "pos": t.pos_,
                    "tag": t.tag_,
                    "dep": t.dep_,
                    "head": int(t.head.i),
                    "is_sent_start": None if t.is_sent_start is None else bool(t.is_sent_start),
                    "ent_iob": t.ent_iob_,
                    "ent_type": t.ent_type_,
                }
                for t in doc
            ],
            "sentences": [
                {
                    "start": int(s.start),
                    "end": int(s.end),
                    "start_char": int(s.start_char),
                    "end_char": int(s.end_char),
                    "text": s.text,
                }
                for s in doc.sents
            ],
            "entities": [
                {
                    "start": int(e.start),
                    "end": int(e.end),
                    "start_char": int(e.start_char),
                    "end_char": int(e.end_char),
                    "label": e.label_,
                    "text": e.text,
                }
                for e in doc.ents
            ],
        }

        if "id" in input:
            out["id"] = input["id"]

        return out

    def _grab_nlp(self, model: str, disable: tuple[str, ...]):
        key = Spacy.ModelKey(model, disable)
        cached = self._nlp_cache.get(key)
        if cached is not None:
            return cached

        try:
            nlp = spacy.load(model, disable=list(disable))
        except OSError:
            if os.path.exists(model):
                raise
            spacy.cli.download(model)
            nlp = spacy.load(model, disable=list(disable))

        self._nlp_cache[key] = nlp
        return nlp

    class ModelKey:
        __slots__ = ("model", "disable")

        def __init__(self, model: str, disable: tuple[str, ...]):
            self.model = model
            self.disable = disable

        def __hash__(self) -> int:
            return hash((self.model, self.disable))

        def __eq__(self, other: object) -> bool:
            return isinstance(other, Spacy.ModelKey) and self.model == other.model and self.disable == other.disable
