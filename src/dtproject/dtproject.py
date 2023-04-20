import copy
import glob
import os
import re
import traceback
from pathlib import Path
from types import SimpleNamespace
from typing import Optional, List

import requests
from requests import Response

from dockertown import Image

from dockertown.exceptions import NoSuchImage

from .configurations import parse_configurations
from .exceptions import \
    RecipeProjectNotFound, \
    DTProjectNotFound, \
    MalformedDTProject, \
    UnsupportedDTProjectVersion, \
    NotFound

from .constants import *
from .recipe import get_recipe_project_dir, update_recipe, clone_recipe
from .utils.docker import docker_client
from .utils.misc import run_cmd, git_remote_url_to_https, assert_canonical_arch


class DTProject:
    """
    Class representing a DTProject on disk.
    """

    def __init__(self, path: str):
        self._adapters = []
        self._repository = None
        # use `fs` adapter by default
        self._path = os.path.abspath(path)
        self._adapters.append("fs")
        # use `dtproject` adapter (required)
        self._project_info = self._get_project_info(self._path)
        self._type = self._project_info["TYPE"]
        self._type_version = self._project_info["TYPE_VERSION"]
        self._version = self._project_info["VERSION"]
        self._adapters.append("dtproject")
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

    @property
    def path(self):
        return self._path

    @property
    def name(self):
        return (self._repository.name if self._repository else os.path.basename(self.path)).lower()

    @property
    def metadata(self) -> Dict[str, str]:
        return copy.deepcopy(self._project_info)

    @property
    def type(self):
        return self._type

    @property
    def type_version(self):
        return self._type_version

    @property
    def distro(self):
        return self._repository.branch.split("-")[0] if self._repository else "latest"

    @property
    def version(self):
        return self._version

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
    def needs_recipe(self) -> bool:
        return self.type == "template-exercise"

    @property
    def recipe_dir(self) -> Optional[str]:
        if not self.needs_recipe:
            return None
        return (
            self._custom_recipe_dir
            if self._custom_recipe_dir
            else get_recipe_project_dir(
                self.metadata["RECIPE_REPOSITORY"],
                self._recipe_version or self.metadata["RECIPE_BRANCH"],
                self.metadata["RECIPE_LOCATION"],
            )
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
            cloned: bool = clone_recipe(
                self.metadata["RECIPE_REPOSITORY"],
                self._recipe_version or self.metadata["RECIPE_BRANCH"],
                self.metadata["RECIPE_LOCATION"],
            )
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
            return update_recipe(
                self.metadata["RECIPE_REPOSITORY"],
                self._recipe_version or self.metadata["RECIPE_BRANCH"],
                self.metadata["RECIPE_LOCATION"],
            )  # raises: UserError if the recipe has not been cloned
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
        inspect = self.image_metadata(endpoint, arch=arch, owner=owner, version=version, registry=registry)

        # remove useless data
        del inspect["ContainerConfig"]
        del inspect["Config"]["Labels"]
        # compile metadata
        meta = {
            "version": "1.0",
            "tag": image_tag,
            "image": inspect,
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
        if int(self._type_version) < 2:
            raise NotImplementedError(
                "Project configurations were introduced with template "
                "types v2. Your project does not support them."
            )
        # ---
        configurations = {}
        if self._type_version == "2":
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
        # root is either a custom given root (remote mounting) or the project path
        root: str = os.path.abspath(root or self.path).rstrip("/")
        # local and destination are fixed given project type and version
        local, destination = TEMPLATE_TO_SRC[self.type][self.type_version](self.name)
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

    def launch_paths(self, root: Optional[str] = None) -> Tuple[str, str]:
        # make sure we support this project version
        if (
                self.type not in TEMPLATE_TO_LAUNCHFILE
                or self.type_version not in TEMPLATE_TO_LAUNCHFILE[self.type]
        ):
            raise UnsupportedDTProjectVersion(
                f"Template {self.type} v{self.type_version} for project {self.path} not supported"
            )
        # ---
        # root is either a custom given root (remote mounting) or the project path
        root: str = os.path.abspath(root or self.path).rstrip("/")
        src, dst = TEMPLATE_TO_LAUNCHFILE[self.type][self.type_version](self.name)
        src = os.path.join(root, src)
        # ---
        return src, dst

    def assets_paths(self, root: Optional[str] = None) -> Tuple[List[str], List[str]]:
        # make sure we support this project version
        if self.type not in TEMPLATE_TO_ASSETS or self.type_version not in TEMPLATE_TO_ASSETS[self.type]:
            raise UnsupportedDTProjectVersion(
                "Template {:s} v{:s} for project {:s} is not supported".format(
                    self.type, self.type_version, self.path
                )
            )
        # ---
        # root is either a custom given root (remote mounting) or the project path
        root: str = os.path.abspath(root or self.path).rstrip("/")
        # local and destination are fixed given project type and version
        local, destination = TEMPLATE_TO_ASSETS[self.type][self.type_version](self.name)
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

    def docs_path(self) -> str:
        # TODO: use this in dts/docs/(env/)build
        # make sure we support this project version
        if self.type not in TEMPLATE_TO_DOCS or self.type_version not in TEMPLATE_TO_DOCS[self.type]:
            raise UnsupportedDTProjectVersion(
                "Template {:s} v{:s} for project {:s} is not supported".format(
                    self.type, self.type_version, self.path
                )
            )
        # ---
        return os.path.join(self.path, TEMPLATE_TO_DOCS[self.type][self.type_version])

    def image_metadata(self, endpoint, arch: str, owner: str, registry: str, version: str):
        client = docker_client(endpoint)
        image_name = self.image(arch=arch, owner=owner, version=version, registry=registry)
        try:
            image: Image = client.image.inspect(image_name)
            return {
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

    @staticmethod
    def _get_repo_info(path):
        sha = run_cmd(["git", "-C", f'"{path}"', "rev-parse", "HEAD"])[0]
        branch = run_cmd(["git", "-C", f'"{path}"', "rev-parse", "--abbrev-ref", "HEAD"])[0]
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
        head_tag = head_tag[0] if head_tag else "ND"
        closest_tag = run_cmd(["git", "-C", f'"{path}"', "tag"])
        closest_tag = closest_tag[-1] if closest_tag else "ND"
        origin_url = run_cmd(["git", "-C", f'"{path}"', "config", "--get", "remote.origin.url"])[0]
        if origin_url.endswith(".git"):
            origin_url = origin_url[:-4]
        if origin_url.endswith("/"):
            origin_url = origin_url[:-1]
        repo = origin_url.split("/")[-1]
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
            "ORIGIN.URL": origin_url,
            "ORIGIN.HTTPS.URL": git_remote_url_to_https(origin_url),
            "INDEX_NUM_MODIFIED": nmodified,
            "INDEX_NUM_ADDED": nadded,
        }
