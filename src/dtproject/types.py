import dataclasses
from typing import List, Optional, TypeVar, Generic, Iterator, Dict

import yaml
from dataclass_wizard import YAMLWizard

from .constants import *
from .utils.misc import ddict

T = TypeVar("T")
EventName = str


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


@dataclasses.dataclass
class ContainerConfiguration(dict):
    """
    This class stores the docker-compose configuration for a single container
    (i.e. a 'service' in the terminology used by docker-compose).

    Attributes:
        __extends__ (List[str]): The name of the container configurations stored in `containers.yaml` layer to extend.
        __plain__ (bool): If True, the container configuration is not extended from any other configuration.
    """
    __extends__: Optional[List[str]] = None
    __plain__: Optional[bool] = None

    def __init__(self, **kwargs):
        super().__init__()
        for key, value in kwargs.items():
            setattr(self, key, value)

    def update(self, other):
        for key, value in other.__dict__.items():
            setattr(self, key, value)

    @property
    def service(self) -> dict:
        return self.__dict__


class LayerContainers(DictLayer[ContainerConfiguration]):
    ITEM_CLASS = ContainerConfiguration


@dataclasses.dataclass
class DevContainerConfiguration(dict):
    """
    Represents a configuration for a development container.

    See https://containers.dev/implementors/json_reference/ for details about each property.

    Attributes:
        container (str): The name of the container configuration stored in the `containers.yaml` layer to use.

    Note:
        This data class inherits from dict, allowing instances to be treated as dictionaries.

    """
    container: str
    remoteEnv: Optional[Dict[str, str]] = None
    remoteUser: Optional[str] = None
    containerUser: Optional[str] = None
    updateRemoteUserUID: Optional[bool] = None
    shutdownAction: Optional[str] = None
    init: Optional[bool] = None
    
    customizations: Optional[Dict[str, Dict]] = None

    # Docker Compose properties
    dockerComposeFile: Optional[str] = None
    service: Optional[str] = None
    workspaceFolder: Optional[str] = None


@dataclasses.dataclass
class Hook:
    command: str
    required: Optional[bool] = False


@dataclasses.dataclass
class LayerHooks(DataClassLayer):
    hooks: Dict[str, List[Hook]] = dataclasses.field(default_factory=lambda: ddict(list))

    def __post_init__(self):
        self.hooks = ddict(list, self.hooks)

    def __iter__(self) -> Iterator[Tuple[EventName, List[Hook]]]:
        for e, h in self.hooks.items():
            yield e, h

    def __getitem__(self, item):
        return self.hooks[item]

    def get(self, __key, _=None) -> list:
        return self.hooks[__key]


class LayerDevContainers(DictLayer[DevContainerConfiguration]):
    ITEM_CLASS = DevContainerConfiguration
