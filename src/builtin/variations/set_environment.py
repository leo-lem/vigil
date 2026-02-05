from core import EnvironmentVariation, BackendEnvironment


class SetEnvironment(EnvironmentVariation):
    def __init__(self, label: str | None = None, **kwargs):
        self.label = label
        self.environment = kwargs

    def vary(self, environment: BackendEnvironment):
        environment.update(self.environment)
