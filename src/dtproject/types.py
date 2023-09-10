import dataclasses
from typing import Optional

import yaml
from dataclass_wizard import YAMLWizard

from .constants import *


@dataclasses.dataclass
class Maintainer:
    name: str
    email: str
    organization: Optional[str] = None

    def __str__(self):
        if self.organization:
            return f"{self.name} @ {self.organization} ({self.email})"
        return f"{self.name} ({self.email})"


@dataclasses.dataclass
class Layer(YAMLWizard):
    pass


@dataclasses.dataclass
class LayerSelf(Layer):
    name: str
    maintainer: Maintainer
    description: str
    version: str
    icon: str = DEFAULT_PROJECT_ICON


@dataclasses.dataclass
class LayerTemplate(Layer):
    name: str
    version: str
    provider: str = DEFAULT_GIT_PROVIDER


@dataclasses.dataclass
class LayerDistro(Layer):
    name: str


@dataclasses.dataclass
class LayerBase(Layer):
    repository: str
    registry: str = DEFAULT_DOCKER_REGISTRY
    organization: str = DUCKIETOWN
    tag: Optional[str] = None


@dataclasses.dataclass
class Recipe:
    repository: str
    provider: str = DEFAULT_GIT_PROVIDER
    organization: str = DUCKIETOWN
    branch: Optional[str] = None
    location: Optional[str] = None


class Recipes(dict):
    def __init__(self, given: bool, **kwargs):
        self._are_given = given
        super().__init__(**kwargs)

    @property
    def default(self) -> Optional[Recipe]:
        return self.get("default", None)

    @property
    def are_given(self) -> bool:
        return self._are_given

    @staticmethod
    def from_yaml_file(path: str) -> 'Recipes':
        with open(path, "rt") as fin:
            recipes: Dict[str, dict] = yaml.safe_load(fin)
        return Recipes(
            given=True, **{n: Recipe(**r) for n, r in recipes.items()}
        )

    @staticmethod
    def empty() -> 'Recipes':
        return Recipes(given=False)
