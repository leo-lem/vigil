from core import InputVariation, Input


class SetInput(InputVariation):
    """ Variation that updates the input dict with the provided key-value pairs. """

    def __init__(self, label: str | None = None, **kwargs):
        self.label = label
        self.input = kwargs

    def vary(self, inputs: list[Input]):
        for input in inputs:
            if not isinstance(input, dict):
                raise TypeError("SetInput expects dict inputs.")
            input.update(self.input)
