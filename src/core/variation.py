from __future__ import annotations

from copy import deepcopy
from enum import Enum

from .__types__ import Input
from .backend import Backend, BackendFunction, BackendEnvironment


class Variation:
    """
    Abstract base class for controlled variation.

    Variations transform a batch of inputs into another batch.
    Depending on intent, they may also update backend configuration.
    """
    intent: Variation.Intent

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def apply(self, inputs: list[Input], backend: Backend) -> list[Input]:
        raise NotImplementedError

    class Intent(str, Enum):
        """
        Declares the source domain a variation targets.

        - INPUT: modifies the input artefact(s) presented to the backend
        - FUNCTION: modifies the executed function configuration
        - ENVIRONMENT: modifies execution environment conditions
        """
        INPUT = "input"
        FUNCTION = "function"
        ENVIRONMENT = "environment"


class InputVariation(Variation):
    """ Variation that targets input artefacts only. """

    intent = Variation.Intent.INPUT

    def apply(self, inputs: list[Input], backend: Backend) -> list[Input]:
        copied = deepcopy(inputs)
        returned = self.vary(copied)
        return returned if returned is not None else copied

    def vary(self, inputs: list[Input]) -> list[Input] | None:
        """ Either mutate `inputs` in-place and return None, or return a new list of inputs. """
        raise NotImplementedError


class FunctionVariation(Variation):
    """
    Variation that targets function-level configuration only.

    Updates the backend's function configuration and passes inputs through.
    No teardown is required. The function config is applied per compute call.
    """

    intent = Variation.Intent.FUNCTION

    def apply(self, inputs: list[Input], backend: Backend) -> list[Input]:
        copied = deepcopy(backend.function)
        returned = self.vary(copied)
        backend.set_function(returned if returned is not None else copied)
        return inputs

    def vary(self, function: BackendFunction) -> BackendFunction | None:
        """ Either mutate `function` in-place and return None, or return a new function. """
        raise NotImplementedError


class EnvironmentVariation(Variation):
    """
    Variation that targets execution environment configuration only.

    Updates the backend's environment configuration and passes inputs through.
    Cleanup is handled by the backend's `run(..., cleanup=...)` behaviour.
    """

    intent = Variation.Intent.ENVIRONMENT

    def apply(self, inputs: list[Input], backend: Backend) -> list[Input]:
        copied = deepcopy(backend.environment)
        returned = self.vary(copied)
        backend.set_environment(returned if returned is not None else copied)
        return inputs

    def vary(self, environment: BackendEnvironment) -> BackendEnvironment | None:
        """ Either mutate `environment` in-place and return None, or return a new environment. """
        raise NotImplementedError
