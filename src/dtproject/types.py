import dataclasses
from typing import Optional, TypeVar, Generic

import yaml
from dataclass_wizard import YAMLWizard

from .constants import *


T = TypeVar("T")


class Layer:
    pass


class DictLayer(Layer, Generic[T], dict):
    ITEM_CLASS: type = None

    def __init__(self, given: bool, **kwargs):
        self._are_given = given
        super().__init__(**kwargs)

    @property
    def default(self) -> Optional[T]:
        return self.get("default", None)

    @property
    def are_given(self) -> bool:
        return self._are_given

    @property
    def is_empty(self) -> bool:
        return dict.__len__(self) <= 0

    def has(self, recipe: str) -> bool:
        return recipe in self

    @classmethod
    def from_yaml_file(cls, path: str) -> 'DictLayer':
        with open(path, "rt") as fin:
            d: Dict[str, dict] = yaml.safe_load(fin)
        return cls(given=True, **{n: cls.ITEM_CLASS(**r) for n, r in d.items()})

    @classmethod
    def empty(cls) -> 'DictLayer':
        return cls(given=False)


@dataclasses.dataclass
class DataClassLayer(YAMLWizard, Layer):
    pass


@dataclasses.dataclass
class LayerFormat(DataClassLayer):
    version: int


@dataclasses.dataclass
class LayerOptions(DataClassLayer):
    needs_recipe: bool = False


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
class LayerSelf(DataClassLayer):
    name: str
    maintainer: Maintainer
    description: str
    version: str
    icon: str = DEFAULT_PROJECT_ICON


@dataclasses.dataclass
class LayerTemplate(DataClassLayer):
    name: Optional[str]
    version: str
    provider: str = DEFAULT_GIT_PROVIDER


@dataclasses.dataclass
class LayerDistro(DataClassLayer):
    name: str


@dataclasses.dataclass
class LayerBase(DataClassLayer):
    repository: str
    registry: Optional[str] = None
    organization: str = DUCKIETOWN
    tag: Optional[str] = None


@dataclasses.dataclass
class Recipe:
    repository: str
    branch: str
    provider: str = DEFAULT_GIT_PROVIDER
    organization: str = DUCKIETOWN
    location: Optional[str] = None

    def copy(self) -> 'Recipe':
        return Recipe(**dataclasses.asdict(self))


class LayerRecipes(DictLayer[Recipe]):
    ITEM_CLASS = Recipe


class ContainerConfiguration(dict):
    pass


class LayerContainers(DictLayer[ContainerConfiguration]):
    ITEM_CLASS = ContainerConfiguration


class DevContainerConfiguration(dict):
    pass


class LayerDevContainers(DictLayer[DevContainerConfiguration]):
    ITEM_CLASS = DevContainerConfiguration
