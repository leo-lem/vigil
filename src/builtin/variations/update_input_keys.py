from core import InputVariation, Input


class UpdateInputKeys(InputVariation):
    def __init__(self, input: dict, label: str | None = None):
        self.label = label
        self.input = input

    def vary(self, inputs: list[Input]):
        for input in inputs:
            if not isinstance(input, dict):
                raise TypeError("UpdateInputKeys expects dict inputs.")
            input.update(self.input)
