import copy
import dataclasses
import glob
import os
import re
import traceback
from abc import abstractmethod
from pathlib import Path
from subprocess import CalledProcessError
from types import SimpleNamespace
from typing import Optional, List, Union, Set, cast, Any

import requests
import yaml
from requests import Response

from dockertown import Image

from dockertown.exceptions import NoSuchImage

from .configurations import parse_configurations
from .exceptions import \
    RecipeProjectNotFound, \
    DTProjectNotFound, \
    MalformedDTProject, \
    UnsupportedDTProjectVersion, \
    NotFound, \
    InconsistentDTProject

from .constants import *
from .types import LayerSelf, LayerTemplate, LayerDistro, LayerBase, LayerRecipes, LayerOptions, Recipe, Layer, LayerFormat, LayerContainers, LayerDevContainers
from .utils.docker import docker_client
from .utils.misc import run_cmd, git_remote_url_to_https, assert_canonical_arch, DEPRECATED, \
    load_dependencies_file
from .recipe import get_recipe_project_dir, update_recipe, clone_recipe


class DTProject:
    """
    Class representing a DTProject on disk.
    """

    @dataclasses.dataclass
    class Layers:
        format: LayerFormat
        self: LayerSelf
        distro: LayerDistro
        base: LayerBase
        options: LayerOptions = dataclasses.field(default_factory=LayerOptions)
        template: Optional[LayerTemplate] = None
        recipes: LayerRecipes = dataclasses.field(default_factory=LayerRecipes.empty)
        containers: LayerContainers = dataclasses.field(default_factory=LayerContainers.empty)
        devcontainers: LayerDevContainers = dataclasses.field(default_factory=LayerDevContainers.empty)

        def as_dict(self) -> Dict[str, dict]:
            return dataclasses.asdict(self)

    REQUIRED_LAYERS = {"format": LayerFormat, "self": LayerSelf, "distro": LayerDistro, "base": LayerBase}
    OPTIONAL_LAYERS = {
        "template": LayerTemplate,
        "recipes": LayerRecipes,
        "options": LayerOptions,
        "containers": LayerContainers,
        "devcontainers": LayerDevContainers,
    }
    KNOWN_LAYERS = {**REQUIRED_LAYERS, **OPTIONAL_LAYERS}

    def __init__(self, path: str, recipe: Optional[str] = None):
        self._adapters = []
        self._repository = None
        # use `fs` adapter by default
        self._path = os.path.abspath(path)
        self._adapters.append("fs")
        # recipe info
        self._custom_recipe_dir: Optional[str] = None
        self._recipe_version: Optional[str] = None
        # use `git` adapter if available
        if os.path.isdir(os.path.join(self._path, ".git")):
            repo_info = self._get_repo_info(self._path)
            self._repository = SimpleNamespace(
                name=repo_info["REPOSITORY"],
                sha=repo_info["SHA"],
                detached=repo_info["BRANCH"] == "HEAD",
                branch=repo_info["BRANCH"],
                head_version=repo_info["VERSION.HEAD"],
                closest_version=repo_info["VERSION.CLOSEST"],
                repository_url=repo_info["ORIGIN.URL"],
                repository_page=repo_info["ORIGIN.HTTPS.URL"],
                index_nmodified=repo_info["INDEX_NUM_MODIFIED"],
                index_nadded=repo_info["INDEX_NUM_ADDED"],
            )
            self._adapters.append("git")
        # at this point we initialize the proper subclass
        for DTProjectSubClass in [DTProjectV1, DTProjectV2, DTProjectV3, DTProjectV4]:
            if DTProjectSubClass.is_instance_of(path):
                self.__class__ = DTProjectSubClass
                # noinspection PyTypeChecker
                DTProjectSubClass.__init__(self, path, recipe=recipe)
                return
        # if we are here, it means that this candidate project did not match any project version
        raise DTProjectNotFound(f"No valid DTProject found at '{path}'")

    @property
    def path(self) -> str:
        return self._path

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def format(self) -> LayerFormat:
        pass

    @property
    @abstractmethod
    def options(self) -> LayerOptions:
        pass

    @property
    @abstractmethod
    def base_info(self) -> LayerBase:
        pass

    @property
    @abstractmethod
    def template_info(self) -> LayerTemplate:
        pass

    @property
    @abstractmethod
    def containers(self) -> LayerContainers:
        pass

    @property
    @abstractmethod
    def devcontainers(self) -> LayerDevContainers:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def maintainer(self) -> str:
        pass

    @property
    @abstractmethod
    def icon(self) -> str:
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        pass

    @property
    @abstractmethod
    def type(self) -> Optional[str]:
        pass

    @property
    @abstractmethod
    def type_version(self) -> str:
        pass

    @property
    @abstractmethod
    @DEPRECATED
    def metadata(self) -> Dict[str, str]:
        pass

    @property
    @abstractmethod
    def layers(self) -> Layers:
        pass

    @property
    @abstractmethod
    def distro(self) -> str:
        pass

    @property
    @abstractmethod
    def base_registry(self) -> Optional[str]:
        pass

    @property
    @abstractmethod
    def base_repository(self) -> Optional[str]:
        pass

    @property
    @abstractmethod
    def base_organization(self) -> Optional[str]:
        pass

    @property
    @abstractmethod
    def base_tag(self) -> Optional[str]:
        pass

    @property
    def build_args(self) -> Dict[str, Any]:
        return {}

    @property
    def needs_recipe(self) -> bool:
        return self.options.needs_recipe

    @property
    def head_version(self):
        return self._repository.head_version if self._repository else "latest"

    @property
    def closest_version(self):
        return self._repository.closest_version if self._repository else "latest"

    @property
    def version_name(self):
        return (self._repository.branch if self._repository.branch != "HEAD" else self.head_version) \
            if self._repository else "latest"

    @property
    def safe_version_name(self) -> str:
        return re.sub(r"[^\w\-.]", "-", self.version_name)

    @property
    def url(self):
        return self._repository.repository_page if self._repository else None

    @property
    def sha(self):
        return self._repository.sha if self._repository else "ND"

    @property
    def adapters(self):
        return copy.copy(self._adapters)

    @property
    @abstractmethod
    def recipes(self) -> Dict[str, Recipe]:
        pass

    @property
    @abstractmethod
    def recipe_info(self) -> Optional[Recipe]:
        pass

    @property
    def recipe_dir(self) -> Optional[str]:
        if not self.needs_recipe:
            return None
        return (
            self._custom_recipe_dir
            if self._custom_recipe_dir
            else get_recipe_project_dir(self.recipe_info)
        )

    @property
    def recipe(self) -> Optional["DTProject"]:
        # load recipe project
        return DTProject(self.recipe_dir) if self.needs_recipe else None

    @property
    def dockerfile(self) -> str:
        if self.needs_recipe:
            # this project needs a recipe to build
            recipe: DTProject = self.recipe
            return recipe.dockerfile
        # this project carries its own Dockerfile
        return os.path.join(self.path, "Dockerfile")

    @property
    def vscode_dockerfile(self) -> Optional[str]:
        # this project's vscode Dockerfile
        vscode_dockerfile: str = os.path.join(self.path, "Dockerfile.vscode")
        if os.path.exists(vscode_dockerfile):
            return vscode_dockerfile
        # it might be in the recipe (if any)
        if self.needs_recipe:
            # this project needs a recipe to build
            recipe: DTProject = self.recipe
            return recipe.vscode_dockerfile
        # this project does not have a Dockerfile.vscode
        return None

    @property
    def vnc_dockerfile(self) -> Optional[str]:
        # this project's vnc Dockerfile
        vnc_dockerfile: str = os.path.join(self.path, "Dockerfile.vnc")
        if os.path.exists(vnc_dockerfile):
            return vnc_dockerfile
        # it might be in the recipe (if any)
        if self.needs_recipe:
            # this project needs a recipe to build
            recipe: DTProject = self.recipe
            return recipe.vnc_dockerfile
        # this project does not have a Dockerfile.vnc
        return None

    @property
    def launchers(self) -> List[str]:
        # read project template version
        try:
            project_template_ver = int(self.type_version)
        except ValueError:
            project_template_ver = -1
        # search for launchers (template v2+)
        if project_template_ver < 2:
            raise NotImplementedError("Only projects with template type v2+ support launchers.")
        # we return launchers from both recipe and meat
        paths: List[str] = [self.path]
        if self.needs_recipe:
            paths.append(self.recipe.path)
        # find launchers
        launchers = []
        for root in paths:
            launchers_dir = os.path.join(root, "launchers")
            if not os.path.exists(launchers_dir):
                continue
            files = [
                os.path.join(launchers_dir, f)
                for f in os.listdir(launchers_dir)
                if os.path.isfile(os.path.join(launchers_dir, f))
            ]

            def _has_shebang(f):
                with open(f, "rt") as fin:
                    return fin.readline().startswith("#!")

            launchers = [Path(f).stem for f in files if os.access(f, os.X_OK) or _has_shebang(f)]
        # ---
        return launchers

    def set_recipe_dir(self, path: str):
        self._custom_recipe_dir = path

    def set_recipe_version(self, branch: str):
        self._recipe_version = branch

    def ensure_recipe_exists(self):
        if not self.needs_recipe:
            return
        # clone the project specified recipe (if necessary)
        if not os.path.exists(self.recipe_dir):
            cloned: bool = clone_recipe(self.recipe_info)
            if not cloned:
                raise RecipeProjectNotFound(f"Recipe repository could not be downloaded.")
        # make sure the recipe exists
        if not os.path.exists(self.recipe_dir):
            raise RecipeProjectNotFound(f"Recipe not found at '{self.recipe_dir}'")

    def ensure_recipe_updated(self) -> bool:
        return self.update_cached_recipe()

    def update_cached_recipe(self) -> bool:
        """Update recipe if not using custom given recipe"""
        if self.needs_recipe and not self._custom_recipe_dir:
            return update_recipe(self.recipe_info)  # raises: UserError if the recipe has not been cloned
        return False

    def is_release(self):
        if not self.is_clean():
            return False
        if self._repository and self.head_version != "ND":
            return True
        return False

    def is_clean(self):
        if self._repository:
            return (self._repository.index_nmodified + self._repository.index_nadded) == 0
        return True

    def is_dirty(self):
        return not self.is_clean()

    def is_detached(self):
        return self._repository.detached if self._repository else False

    def image(
            self,
            *,
            arch: str,
            registry: str,
            owner: str,
            version: Optional[str] = None,
            loop: bool = False,
            docs: bool = False,
            extra: Optional[str] = None,
    ) -> str:
        assert_canonical_arch(arch)
        loop = "-LOOP" if loop else ""
        docs = "-docs" if docs else ""
        extra = f"-{extra}" if extra else ""
        if version is None:
            version = self.safe_version_name
        return f"{registry}/{owner}/{self.name}:{version}{extra}{loop}{docs}-{arch}"

    def image_vscode(
            self,
            *,
            arch: str,
            registry: str,
            owner: str,
            version: Optional[str] = None,
            docs: bool = False,
    ) -> str:
        return self.image(
            arch=arch, registry=registry, owner=owner, version=version, docs=docs, extra="vscode"
        )

    def image_vnc(
            self,
            *,
            arch: str,
            registry: str,
            owner: str,
            version: Optional[str] = None,
            docs: bool = False,
    ) -> str:
        return self.image(arch=arch, registry=registry, owner=owner, version=version, docs=docs, extra="vnc")

    def image_release(
            self,
            *,
            arch: str,
            owner: str,
            registry: str,
            docs: bool = False,
    ) -> str:
        if not self.is_release():
            raise ValueError("The project repository is not in a release state")
        assert_canonical_arch(arch)
        docs = "-docs" if docs else ""
        version = re.sub(r"[^\w\-.]", "-", self.head_version)
        return f"{registry}/{owner}/{self.name}:{version}{docs}-{arch}"

    def manifest(
            self,
            *,
            registry: str,
            owner: str,
            version: Optional[str] = None,
    ) -> str:
        if version is None:
            version = re.sub(r"[^\w\-.]", "-", self.version_name)

        return f"{registry}/{owner}/{self.name}:{version}"

    def ci_metadata(self, endpoint, *, arch: str, registry: str, owner: str, version: str):
        image_tag = self.image(arch=arch, owner=owner, version=version, registry=registry)
        try:
            configurations = self.configurations()
        except NotImplementedError:
            configurations = {}
        # do docker inspect
        image: dict = self.image_metadata(
            endpoint,
            arch=arch,
            owner=owner,
            version=version,
            registry=registry
        )

        # compile metadata
        meta = {
            "version": "1.0",
            "tag": image_tag,
            "image": image,
            "project": {
                "path": self.path,
                "name": self.name,
                "type": self.type,
                "type_version": self.type_version,
                "distro": self.distro,
                "version": self.version,
                "head_version": self.head_version,
                "closest_version": self.closest_version,
                "version_name": self.version_name,
                "url": self.url,
                "sha": self.sha,
                "adapters": self.adapters,
                "is_release": self.is_release(),
                "is_clean": self.is_clean(),
                "is_dirty": self.is_dirty(),
                "is_detached": self.is_detached(),
            },
            "configurations": configurations,
            "labels": self.image_labels(
                endpoint,
                arch=arch,
                registry=registry,
                owner=owner,
                version=version,
            ),
        }
        # ---
        return meta

    def configurations(self) -> dict:
        if int(self.type_version) < 2:
            raise NotImplementedError(
                "Project configurations were introduced with template "
                "types v2. Your project does not support them."
            )
        # ---
        configurations = {}
        if self.type_version == "2":
            configurations_file = os.path.join(self._path, "configurations.yaml")
            if os.path.isfile(configurations_file):
                configurations = parse_configurations(configurations_file)
        # ---
        return configurations

    def configuration(self, name: str) -> dict:
        configurations = self.configurations()
        if name not in configurations:
            raise KeyError(f"Configuration with name '{name}' not found.")
        return configurations[name]

    def code_paths(self, root: Optional[str] = None) -> Tuple[List[str], List[str]]:
        # make sure we support this project version
        if self.type not in TEMPLATE_TO_SRC or self.type_version not in TEMPLATE_TO_SRC[self.type]:
            raise UnsupportedDTProjectVersion(
                "Template {:s} v{:s} for project {:s} is not supported".format(
                    self.type, self.type_version, self.path
                )
            )
        # ---
        template_src: Optional[Callable] = TEMPLATE_TO_SRC[self.type][self.type_version]
        # no template, no known code
        if template_src is None:
            return [], []
        # root is either a custom given root (remote mounting) or the project path
        root: str = os.path.abspath(root or self.path).rstrip("/")
        # local and destination are fixed given project type and version
        local, destination = template_src(self.name)
        # 'local' can be a pattern
        if local.endswith("*"):
            # resolve 'local' with respect to the project path
            local_abs: str = os.path.join(self.path, local)
            # resolve pattern
            locals = glob.glob(local_abs)
            # we only support mounting directories
            locals = [loc for loc in locals if os.path.isdir(loc)]
            # replace 'self.path' prefix with 'root'
            locals = [os.path.join(root, os.path.relpath(loc, self.path)) for loc in locals]
            # destinations take the stem of the source
            destinations = [os.path.join(destination, Path(loc).stem) for loc in locals]
        else:
            # by default, there is only one local and one destination
            locals: List[str] = [os.path.join(root, local)]
            destinations: List[str] = [destination]
        # ---
        return locals, destinations

    def launch_paths(self, root: Optional[str] = None) -> Tuple[List[str], List[str]]:
        # make sure we support this project version
        if self.type not in TEMPLATE_TO_LAUNCHFILE or \
                self.type_version not in TEMPLATE_TO_LAUNCHFILE[self.type]:
            raise UnsupportedDTProjectVersion(
                f"Template {self.type} v{self.type_version} for project {self.path} not supported"
            )
        # ---
        template_launch: Optional[Callable] = TEMPLATE_TO_LAUNCHFILE[self.type][self.type_version]
        # no template, no known launchers
        if template_launch is None:
            return [], []
        # root is either a custom given root (remote mounting) or the project path
        root: str = os.path.abspath(root or self.path).rstrip("/")
        src, dst = template_launch(self.name)
        src = os.path.join(root, src)
        # ---
        return [src], [dst]

    def assets_paths(self, root: Optional[str] = None) -> Tuple[List[str], List[str]]:
        # make sure we support this project version
        if self.type not in TEMPLATE_TO_ASSETS or self.type_version not in TEMPLATE_TO_ASSETS[self.type]:
            raise UnsupportedDTProjectVersion(
                "Template {:s} v{:s} for project {:s} is not supported".format(
                    self.type, self.type_version, self.path
                )
            )
        # ---
        template_assets: Optional[Callable] = TEMPLATE_TO_ASSETS[self.type][self.type_version]
        # no template, no known assets path
        if template_assets is None:
            return [], []
        # root is either a custom given root (remote mounting) or the project path
        root: str = os.path.abspath(root or self.path).rstrip("/")
        # local and destination are fixed given project type and version
        local, destination = template_assets(self.name)
        # 'local' can be a pattern
        if local.endswith("*"):
            # resolve 'local' with respect to the project path
            local_abs: str = os.path.join(self.path, local)
            # resolve pattern
            locals = glob.glob(local_abs)
            # we only support mounting directories
            locals = [loc for loc in locals if os.path.isdir(loc)]
            # replace 'self.path' prefix with 'root'
            locals = [os.path.join(root, os.path.relpath(loc, self.path)) for loc in locals]
            # destinations take the stem of the source
            destinations = [os.path.join(destination, Path(loc).stem) for loc in locals]
        else:
            # by default, there is only one local and one destination
            locals: List[str] = [os.path.join(root, local)]
            destinations: List[str] = [destination]
        # ---
        return locals, destinations

    def docs_path(self) -> Optional[str]:
        # make sure we support this project version
        if self.type not in TEMPLATE_TO_DOCS or self.type_version not in TEMPLATE_TO_DOCS[self.type]:
            raise UnsupportedDTProjectVersion(
                "Template {:s} v{:s} for project {:s} is not supported".format(
                    self.type, self.type_version, self.path
                )
            )
        # ---
        template_docs: Optional[str] = TEMPLATE_TO_DOCS[self.type][self.type_version]
        # no template, no known docs
        if template_docs is None:
            return None
        # ---
        return os.path.join(self.path, template_docs)

    def image_metadata(self, endpoint, arch: str, owner: str, registry: str, version: str):
        client = docker_client(endpoint)
        image_name = self.image(arch=arch, owner=owner, version=version, registry=registry)
        try:
            image: Image = client.image.inspect(image_name)
            metadata: dict = {
                # - id: str
                "id": image.id,
                # - repo_tags: List[str]
                "repo_tags": image.repo_tags,
                # - repo_digests: List[str]
                "repo_digests": image.repo_digests,
                # - parent: str
                "parent": image.parent,
                # - comment: str
                "comment": image.comment,
                # - created: datetime
                "created": image.created.isoformat(),
                # - container: str
                "container": image.container,
                # - container_config: ContainerConfig
                "container_config": image.container_config.dict(),
                # - docker_version: str
                "docker_version": image.docker_version,
                # - author: str
                "author": image.author,
                # - config: ContainerConfig
                "config": image.config.dict(),
                # - architecture: str
                "architecture": image.architecture,
                # - os: str
                "os": image.os,
                # - os_version: str
                "os_version": image.os_version,
                # - size: int
                "size": image.size,
                # - virtual_size: int
                "virtual_size": image.virtual_size,
                # - graph_driver: ImageGraphDriver
                "graph_driver": image.graph_driver.dict(),
                # - root_fs: ImageRootFS
                "root_fs": image.root_fs.dict(),
                # - metadata: Dict[str, str]
                "metadata": image.metadata,
            }
            # sanitize posizpath objects
            metadata["container_config"]["working_dir"] = str(metadata["container_config"]["working_dir"])
            metadata["config"]["working_dir"] = str(metadata["config"]["working_dir"])
            # ---
            return metadata
        except NoSuchImage:
            raise Exception(f"Cannot get image metadata for {image_name!r}: \n {traceback.format_exc()}")

    def image_labels(self, endpoint, *, arch: str, owner: str, registry: str, version: str):
        metadata: dict = self.image_metadata(
            endpoint, arch=arch, owner=owner, registry=registry, version=version
        )
        return metadata["config"]["labels"]

    def remote_image_metadata(self, arch: str, owner: str, registry: str) -> Dict:
        assert_canonical_arch(arch)
        tag = f"{self.version_name}-{arch}"
        # compile DCSS url
        url: str = DCSS_DOCKER_IMAGE_METADATA.format(
            registry=registry,
            organization=owner,
            repository=self.name,
            tag=tag
        )
        # fetch json
        response: Response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise NotFound(f"Remote image '{registry}/{owner}/{self.name}:{tag}' not found")
        else:
            response.raise_for_status()

    def apt_dependencies(self, comments: bool = False) -> List[str]:
        dependencies_fpath: str = os.path.join(self.path, "dependencies-apt.txt")
        return load_dependencies_file(dependencies_fpath, comments=comments)

    def py3_dependencies(self, comments: bool = False, ) -> List[str]:
        dependencies_fpath: str = os.path.join(self.path, "dependencies-py3.txt")
        return load_dependencies_file(dependencies_fpath, comments=comments)

    def py3_dependencies_dt(self, comments: bool = False, ) -> List[str]:
        dependencies_fpath: str = os.path.join(self.path, "dependencies-py3.dt.txt")
        return load_dependencies_file(dependencies_fpath, comments=comments)

    @staticmethod
    def _get_repo_info(path):
        # get current SHA
        try:
            sha = run_cmd(["git", "-C", f'"{path}"', "rev-parse", "HEAD"])[0]
        except CalledProcessError as e:
            if e.returncode == 128:
                # no commits yet
                sha = "ND"
            else:
                raise e
        # get branch name
        branch = run_cmd(["git", "-C", f'"{path}"', "branch", "--show-current"])[0]
        # head tag
        try:
            head_tag = run_cmd(
                [
                    "git",
                    "-C",
                    f'"{path}"',
                    "describe",
                    "--exact-match",
                    "--tags",
                    "HEAD",
                    "2>/dev/null",
                    "||",
                    ":",
                ]
            )
        except CalledProcessError as e:
            if sha == "ND":
                # there is no HEAD
                head_tag = None
            else:
                raise e
        head_tag = head_tag[0] if head_tag else "ND"
        closest_tag = run_cmd(["git", "-C", f'"{path}"', "tag"])
        closest_tag = closest_tag[-1] if closest_tag else "ND"
        repo = None
        # get the origin url
        try:
            origin_url = run_cmd(["git", "-C", f'"{path}"', "config", "--get", "remote.origin.url"])[0]
            if origin_url.endswith(".git"):
                origin_url = origin_url[:-4]
            if origin_url.endswith("/"):
                origin_url = origin_url[:-1]
            repo = origin_url.split("/")[-1]
        except CalledProcessError as e:
            if e.returncode == 1:
                origin_url = None
            else:
                raise e
        # get info about current git INDEX
        porcelain = ["git", "-C", f'"{path}"', "status", "--porcelain"]
        modified = run_cmd(porcelain + ["--untracked-files=no"])
        nmodified = len(modified)
        added = run_cmd(porcelain)
        # we are not counting files with .resolved extension
        added = list(filter(lambda f: not f.endswith(".resolved"), added))
        nadded = len(added)
        # return info
        return {
            "REPOSITORY": repo,
            "SHA": sha,
            "BRANCH": branch,
            "VERSION.HEAD": head_tag,
            "VERSION.CLOSEST": closest_tag,
            "ORIGIN.URL": origin_url or "ND",
            "ORIGIN.HTTPS.URL": git_remote_url_to_https(origin_url) if origin_url else None,
            "INDEX_NUM_MODIFIED": nmodified,
            "INDEX_NUM_ADDED": nadded,
        }

    @classmethod
    @abstractmethod
    def is_instance_of(cls, path: str) -> bool:
        pass


class DTProjectV4(DTProject):
    """
    Class representing a DTProject on disk.
    """

    # noinspection PyMissingConstructor
    def __init__(self, path: str, recipe: Optional[str] = None):
        # use `dtproject` adapter (required)
        self._layers: DTProject.Layers = self._load_layers(path)
        self._adapters.append("dtproject")
        # consistency checks
        # - we need recipes but none are given
        if self.needs_recipe and self._layers.recipes.is_empty:
            raise InconsistentDTProject("The project is set to need a recipe (options.needs_recipe=True) but "
                                        "no recipes are defined in the recipes layer.")
        # - we don't need recipes but some are given
        if not self.needs_recipe and not self._layers.recipes.is_empty:
            raise InconsistentDTProject("The project is set NOT to need a recipe "
                                        f"(options.needs_recipe=False) but {len(self._layers.recipes)} "
                                        f"recipes are defined in the recipes layer.")
        # - choose a recipe when the project does not need it
        if not self.needs_recipe and recipe is not None:
            raise ValueError(f"Cannot select recipe '{recipe}' on a project that is set NOT to need a recipe "
                             "(options.needs_recipe=False)")
        # - (named) recipe selector
        self._selected_recipe: Optional[str] = None if not self.needs_recipe else (recipe or "default")
        if self._selected_recipe and not self._layers.recipes.has(self._selected_recipe):
            raise ValueError(f"Recipe '{self._selected_recipe}' not defined in this project. Available "
                             f"recipes are: {list(self.recipes.keys())}")

    @property
    def name(self) -> str:
        return self._layers.self.name.lower()

    @property
    def format(self) -> LayerFormat:
        return self._layers.format

    @property
    def options(self) -> LayerOptions:
        return self._layers.options

    @property
    def base_info(self) -> LayerBase:
        return self._layers.base

    @property
    def template_info(self) -> LayerTemplate:
        return self._layers.template

    @property
    def containers(self) -> LayerContainers:
        return self._layers.containers

    @property
    def devcontainers(self) -> LayerDevContainers:
        return self._layers.devcontainers

    @property
    def description(self) -> str:
        return self._layers.self.description

    @property
    def maintainer(self) -> str:
        return str(self._layers.self.maintainer)

    @property
    def icon(self) -> str:
        return self._layers.self.icon

    @property
    def version(self) -> str:
        return self._layers.self.version

    @property
    def type(self) -> str:
        return self._layers.template.name

    @property
    def type_version(self) -> str:
        return self._layers.template.version

    @property
    def distro(self) -> str:
        return self._layers.distro.name

    @property
    def base_registry(self) -> Optional[str]:
        return self._layers.base.registry

    @property
    def base_repository(self) -> Optional[str]:
        return self._layers.base.repository

    @property
    def base_organization(self) -> Optional[str]:
        return self._layers.base.organization

    @property
    def base_tag(self) -> Optional[str]:
        return self._layers.base.tag

    @property
    def build_args(self) -> Dict[str, str]:
        bargs = {
            "DISTRO": self.distro,
            "PROJECT_FORMAT_VERSION": self.format.version,
            "PROJECT_NAME": self.name,
            "PROJECT_DESCRIPTION": self.description,
            "PROJECT_MAINTAINER": self.maintainer,
            "PROJECT_ICON": self.icon,
            "BASE_REPOSITORY": self.base_info.repository,
        }
        if self.base_info.tag is not None:
            bargs["BASE_TAG"] = self.base_info.tag
        if self.base_info.organization is not None:
            bargs["BASE_ORGANIZATION"] = self.base_info.organization
        # ---
        return bargs

    @property
    def metadata(self) -> dict:
        # NOTE: we are only keeping this here for backward compatibility with DTProjects v1,2,3
        return {
            "VERSION": self.version,
            "TYPE": self.type,
            "TYPE_VERSION": self.type_version,
            "PATH": self.path,
        }

    @property
    def layers(self) -> 'DTProject.Layers':
        return self._layers

    @property
    def recipes(self) -> Dict[str, Recipe]:
        return self._layers.recipes

    @property
    def recipe_info(self) -> Optional[Recipe]:
        if not self.needs_recipe:
            return None
        # we already checked that this exists
        recipe: Recipe = self._layers.recipes.get(self._selected_recipe).copy()
        # apply runtime changes
        if self._recipe_version:
            recipe.branch = self._recipe_version
        return recipe

    @staticmethod
    def _load_layers(path: str) -> 'DTProject.Layers':
        if not os.path.exists(path):
            msg = f"The project path {path!r} does not exist."
            raise DTProjectNotFound(msg)
        layers_dir: str = os.path.join(path, "dtproject")
        # if the directory 'dtproject' is missing
        if not os.path.exists(layers_dir):
            msg = f"The path '{path}' does not appear to be a Duckietown project."
            raise DTProjectNotFound(msg)
        # if 'dtproject' is not a directory
        if not os.path.isdir(layers_dir):
            msg = f"The path '{layers_dir}' must be a directory."
            raise MalformedDTProject(msg)

        layers: Dict[str, Union[Layer, dict]] = {}

        # load required layers
        for layer_name, layer_class in DTProject.REQUIRED_LAYERS.items():
            # make sure the <layer>.yaml file is there
            layer_fpath: str = os.path.join(layers_dir, f"{layer_name}.yaml")
            if not os.path.exists(layer_fpath) or not os.path.isfile(layer_fpath):
                msg = f"The file '{layer_fpath}' is missing."
                raise MalformedDTProject(msg)
            layers[layer_name] = layer_class.from_yaml_file(layer_fpath)

        # load optional (but known) layers
        for layer_name, layer_class in DTProject.OPTIONAL_LAYERS.items():
            # load the <layer>.yaml file if it is there
            layer_fpath: str = os.path.join(layers_dir, f"{layer_name}.yaml")
            if not os.path.exists(layer_fpath):
                continue
            if not os.path.isfile(layer_fpath):
                msg = f"The path '{layer_fpath}' must be a regular file."
                raise MalformedDTProject(msg)
            layers[layer_name] = layer_class.from_yaml_file(layer_fpath)

        # load custom layers
        custom_layers: Set[str] = set()
        layer_pattern = os.path.join(path, "dtproject", "*.yaml")
        for layer_fpath in glob.glob(layer_pattern):
            layer_name: str = Path(layer_fpath).stem
            if layer_name not in DTProject.KNOWN_LAYERS:
                with open(layer_fpath, "rt") as fin:
                    layer_content: dict = yaml.safe_load(fin) or {}
                    layers[layer_name] = layer_content
                    custom_layers.add(layer_name)

        # extend layers class
        Layers = dataclasses.make_dataclass(
            'ExtendedLayers',
            fields=[
                (layer, dict, cast(dataclasses.Field, dataclasses.field(default_factory=dict)))
                for layer in custom_layers
            ],
            bases=(DTProject.Layers,)
        )
        # ---
        return Layers(**layers)

    @classmethod
    def is_instance_of(cls, path: str) -> bool:
        if not os.path.exists(path):
            return False
        layers_dir: str = os.path.join(path, "dtproject")
        # if the directory 'dtproject' is missing
        if not os.path.exists(layers_dir):
            return False
        # if 'dtproject' is not a directory
        if not os.path.isdir(layers_dir):
            return False
        # ---
        return True


class DTProjectV1to3(DTProject):
    """
    Class representing a DTProject on disk.
    """

    # noinspection PyMissingConstructor
    def __init__(self, path: str, **_):
        # use `dtproject` adapter (required)
        self._project_info = self._get_project_info(path)
        self._type = self._project_info["TYPE"]
        self._type_version = self._project_info["TYPE_VERSION"]
        self._version = self._project_info["VERSION"]
        self._adapters.append("dtproject")

    @property
    @abstractmethod
    def format(self) -> LayerFormat:
        pass

    @property
    def name(self) -> str:
        return self._project_info.get(
            # a name defined in the dtproject descriptor takes precedence
            "NAME",
            # fallback is repository name and eventually directory name
            self._repository.name if (self._repository and self._repository.name) else
            os.path.basename(self.path)
        ).lower()

    @property
    def options(self) -> LayerOptions:
        return LayerOptions(
            needs_recipe=(self.type == "template-exercise")
        )

    @property
    def base_info(self) -> LayerBase:
        raise NotImplementedError(f"Field 'base' not implemented in DTProject v{self.type_version}")

    @property
    def template_info(self) -> LayerTemplate:
        raise NotImplementedError(f"Field 'template' not implemented in DTProject v{self.type_version}")

    @property
    def containers(self) -> LayerContainers:
        return LayerContainers.empty()

    @property
    def devcontainers(self) -> LayerDevContainers:
        return LayerDevContainers.empty()

    @property
    def description(self) -> str:
        raise NotImplementedError(f"Field 'description' not implemented in DTProject v{self.type_version}")

    @property
    def maintainer(self) -> str:
        raise NotImplementedError(f"Field 'maintainer' not implemented in DTProject v{self.type_version}")

    @property
    def icon(self) -> str:
        raise NotImplementedError(f"Field 'icon' not implemented in DTProject v{self.type_version}")

    @property
    def version(self) -> str:
        return self._version

    @property
    def type(self) -> str:
        return self._type

    @property
    def type_version(self) -> str:
        return self._type_version

    @property
    def distro(self) -> str:
        return self._repository.branch.split("-")[0] if self._repository else "latest"

    @property
    def metadata(self) -> Dict[str, str]:
        return copy.deepcopy(self._project_info)

    @property
    def layers(self) -> 'DTProject.Layers':
        raise NotImplementedError(f"Field 'layers' not implemented in DTProject v{self.type_version}")

    @property
    def recipe_info(self) -> Optional[Recipe]:
        if not self.needs_recipe:
            return None
        organization, repository = self.metadata["RECIPE_REPOSITORY"].split("/")
        return Recipe(
            repository=repository,
            organization=organization,
            branch=self._recipe_version or self.metadata["RECIPE_BRANCH"],
            location=self.metadata["RECIPE_LOCATION"],
        )

    @property
    def recipes(self) -> Dict[str, Recipe]:
        recipes = {}
        if self.needs_recipe:
            recipes["default"] = self.recipe_info
        return recipes

    @staticmethod
    def _get_project_info(path: str):
        if not os.path.exists(path):
            msg = f"The project path {path!r} does not exist."
            raise OSError(msg)

        metafile = os.path.join(path, ".dtproject")
        # if the file '.dtproject' is missing
        if not os.path.exists(metafile):
            msg = f"The path '{path}' does not appear to be a Duckietown project."
            raise DTProjectNotFound(msg)
        # load '.dtproject'
        with open(metafile, "rt") as metastream:
            lines: List[str] = metastream.readlines()
        # empty metadata?
        if not lines:
            msg = f"The metadata file '{metafile}' is empty."
            raise MalformedDTProject(msg)
        # strip lines
        lines = [line.strip() for line in lines]
        # remove empty lines and comments
        lines = [line for line in lines if len(line) > 0 and not line.startswith("#")]
        # parse metadata
        metadata = {key.strip().upper(): val.strip() for key, val in [line.split("=") for line in lines]}
        # look for version-agnostic keys
        for key in REQUIRED_METADATA_KEYS["*"]:
            if key not in metadata:
                msg = f"The metadata file '{metafile}' does not contain the key '{key}'."
                raise MalformedDTProject(msg)
        # validate version
        version = metadata["TYPE_VERSION"]
        if version == "*" or version not in REQUIRED_METADATA_KEYS:
            msg = "The project version %s is not supported." % version
            raise UnsupportedDTProjectVersion(msg)
        # validate metadata
        for key in REQUIRED_METADATA_KEYS[version]:
            if key not in metadata:
                msg = f"The metadata file '{metafile}' does not contain the key '{key}'."
                raise MalformedDTProject(msg)
        # validate metadata keys specific to project type and version
        type = metadata["TYPE"]
        for key in REQUIRED_METADATA_PER_TYPE_KEYS.get(type, {}).get(version, []):
            if key not in metadata:
                msg = f"The metadata file '{metafile}' does not contain the key '{key}'."
                raise MalformedDTProject(msg)
        # metadata is valid
        metadata["PATH"] = path
        return metadata

    @classmethod
    def is_instance_of(cls, path: str) -> bool:
        try:
            cls._get_project_info(path)
        except Exception:
            return False
        return True


# noinspection PyAbstractClass
class DTProjectV1(DTProjectV1to3):

    @property
    def format(self) -> LayerFormat:
        return LayerFormat(version=1)

    @classmethod
    def is_instance_of(cls, path: str) -> bool:
        try:
            DTProjectV1to3._get_project_info(path)
        except Exception:
            return False
        return os.path.isfile(os.path.join(path, "launch.sh")) and os.path.isdir(os.path.join(path, "code"))


# noinspection PyAbstractClass
class DTProjectV2(DTProjectV1to3):

    @property
    def format(self) -> LayerFormat:
        return LayerFormat(version=2)

    @classmethod
    def is_instance_of(cls, path: str) -> bool:
        try:
            DTProjectV1to3._get_project_info(path)
        except Exception:
            return False
        return os.path.isfile(os.path.join(path, ".dtproject")) and \
               not os.path.isfile(os.path.join(path, "dependencies-py3.dt.txt"))


# noinspection PyAbstractClass
class DTProjectV3(DTProjectV1to3):

    @property
    def format(self) -> LayerFormat:
        return LayerFormat(version=3)

    @classmethod
    def is_instance_of(cls, path: str) -> bool:
        try:
            DTProjectV1to3._get_project_info(path)
        except Exception:
            return False
        return os.path.isfile(os.path.join(path, ".dtproject")) and \
               os.path.isfile(os.path.join(path, "dependencies-py3.dt.txt"))
