from core import FunctionVariation, BackendFunction


class SetFunction(FunctionVariation):
    def __init__(self, label: str | None = None, **kwargs):
        self.label = label
        self.function = kwargs

    def vary(self, function: BackendFunction):
        function.update(self.function)
