from __future__ import annotations

from time import time
from typing import TYPE_CHECKING, Any, Callable, TypedDict, NotRequired

from .backend import BackendInput, BackendOutput, BackendFunction, BackendEnvironment

if TYPE_CHECKING:
    from .variation import Variation


class Input(TypedDict):
    id: str
    data: BackendInput
    reference: NotRequired[BackendOutput]


class Slice:
    input: Input
    output: BackendOutput
    function: BackendFunction
    environment: BackendEnvironment
    variation: Variation | None

    timestamp: float
    meta: dict[str, Any]

    def __init__(
        self,
        input: Input,
        output: BackendOutput,
        function: BackendFunction,
        environment: BackendEnvironment,
        variation: Variation | None,
        timestamp: float | None = None,  # automatic timestamp if None
        meta: dict[str, Any] | None = None
    ):
        self.input = input
        self.output = output

        self.function = function
        self.environment = environment
        self.variation = variation

        self.timestamp = time() if timestamp is None else timestamp
        self.meta = meta or {}

    @property
    def id(self) -> str:
        if self.variation is None:
            return f"input-{self.input_id}-reference"
        return f"input-{self.input_id}-variation-{self.variation.name}-{hash(self.variation)}"

    @property
    def input_id(self) -> str:
        return self.input["id"]

    @staticmethod
    def group_by(
        slices: list["Slice"],
        key: Callable[["Slice"], Any],
    ) -> dict[Any, list["Slice"]]:
        groups: dict[Any, list["Slice"]] = {}
        for s in slices:
            k = key(s)
            groups.setdefault(k, []).append(s)
        return groups
