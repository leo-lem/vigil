from core import Backend


class Noop(Backend):
    def update_environment(self, environment) -> None:
        pass  # Intentionally does nothing

    def compute(self, input, function):
        return input
