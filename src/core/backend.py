from __future__ import annotations

from copy import deepcopy
from typing import Any

BackendInput = Any
BackendOutput = Any
BackendFunction = dict[str, Any]
BackendEnvironment = dict[str, Any]


class Backend:
    """
    Backend wrapping a concrete system under evaluation.

    A backend encapsulates a real execution system together with:
    - a fixed base environment configuration, and
    - a fixed base function configuration,

    both defined at construction time.

    The backend itself is configured externally (e.g. via environment
    variables or .env files) and is not described in the specification.
    Specifications only declare inputs, variations, and checks.

    Variations may temporarily modify the backend's environment and/or
    function configuration during execution. The backend provides explicit
    mechanisms to restore both configurations to their base state after
    execution, ensuring isolation between runs.
    """

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def __init__(
        self,
        environment: BackendEnvironment | None = None,
        function: BackendFunction | None = None,
    ):
        """
        Initialise the backend with base environment and function configuration.

        The base configuration defines the identity behaviour of the backend
        and serves as the reset target after variations are applied.

        Subclasses are expected to:
        - resolve all external configuration (e.g. credentials, endpoints)
          before calling this constructor, and
        - treat the provided environment and function dictionaries as the
          authoritative baseline state.

        Parameters
        ----------
        environment:
            Base environment configuration applied eagerly during construction
            via `update_environment`. This typically captures system-level
            state such as project identifiers or runtime context.

        function:
            Base function configuration passed into `compute` on each execution.
            This captures task-level behaviour and is the primary target of
            function-level variation.
        """
        self._base_environment = deepcopy(environment or {})
        self._base_function = deepcopy(function or {})

        self.environment = deepcopy(self._base_environment)
        self.function = deepcopy(self._base_function)
        self.update_environment(deepcopy(self.environment))

    def set_environment(self, environment: BackendEnvironment):
        """
        Update the current environment configuration.

        The provided values are merged into the existing environment and
        applied immediately via `update_environment`.

        This method is typically invoked by variations with environment-level
        intent. Any required teardown or reinitialisation must be handled
        by the backend implementation itself.
        """
        cfg = deepcopy(self.environment)
        cfg.update(environment)
        self.environment = cfg
        self.update_environment(deepcopy(cfg))

    def set_function(self, function: BackendFunction):
        """
        Update the current function configuration.

        The provided values are merged into the existing function configuration.
        Function configuration is not applied eagerly; it is passed verbatim
        into `compute` on each execution.

        This method is typically invoked by variations with function-level
        intent.
        """
        cfg = deepcopy(self.function)
        cfg.update(function)
        self.function = cfg

    def run(self, input: BackendInput, cleanup_env: bool = True, cleanup_fn: bool = True) -> BackendOutput:
        """
        Execute the backend on a single prepared input.

        The input is executed under the current environment and function
        configuration. After execution, the backend may optionally restore
        one or both configurations to their base state.

        Parameters
        ----------
        input:
            Prepared input artefact to execute.

        cleanup_env:
            Whether to restore the environment configuration to its base state
            after execution.

        cleanup_fn:
            Whether to restore the function configuration to its base state
            after execution.

        Returns
        -------
        Any
            The observable output produced by the underlying system.
        """
        try:
            return self.compute(deepcopy(input), deepcopy(self.function))
        finally:
            if cleanup_fn:
                self.function = deepcopy(self._base_function)

            if cleanup_env:
                self.environment = deepcopy(self._base_environment)
                self.update_environment(deepcopy(self.environment))

    def reset(self):
        """
        Restore both environment and function configuration to their base state.

        This provides an explicit reset mechanism independent of execution and
        is primarily intended for engine-level coordination or recovery.
        """
        self.function = deepcopy(self._base_function)
        self.environment = deepcopy(self._base_environment)
        self.update_environment(deepcopy(self.environment))

    def snapshot(self) -> dict[str, Any]:
        """
        Capture a serialisable snapshot of the current backend state.

        The snapshot reflects the effective environment and function
        configuration at the time of capture and is intended for reporting
        and provenance, not for reconstruction.
        """
        return {
            "type": self.__class__.__name__,
            "function": deepcopy(self.function),
            "environment": deepcopy(self.environment),
        }

    def update_environment(self, environment: BackendEnvironment):
        """
        Apply the given environment configuration to the underlying system.

        Implementations must translate the abstract environment dictionary
        into concrete system state and handle any required teardown or
        reinitialisation internally.
        """
        raise NotImplementedError

    def compute(self, input: BackendInput, function: BackendFunction) -> BackendOutput:
        """
        Execute the underlying system for a single input.

        The provided function configuration represents the effective behaviour
        for this execution. Implementations may interpret or partially ignore
        this configuration, but must treat it as immutable for the duration
        of the call.
        """
        raise NotImplementedError
