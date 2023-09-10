import dataclasses
import os.path
import shutil
import subprocess
from contextlib import ContextDecorator
from typing import Optional, Dict, Union, Any
from unittest import skipIf

import yaml
from dtproject.types import LayerBase, Layer, DataClassLayer, DictLayer, LayerOptions, LayerRecipes

ASSETS_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets"))


def get_project_path(name: str) -> str:
    d = os.path.abspath(os.path.join(ASSETS_DIR, "projects", name))
    subprocess.check_output(["git", "config", "--global", "--add", "safe.directory", d])
    assert os.path.exists(d)
    assert os.path.isdir(d)
    return d


def add_git_to_project(name: str, remote: Optional[str] = None, branch: Optional[str] = None):
    path: str = get_project_path(name)
    subprocess.check_output(["git", "init"], cwd=path, stderr=subprocess.PIPE)
    # add remote
    if remote:
        subprocess.check_output(["git", "remote", "add", "origin", remote], cwd=path)
    # add branch
    if branch:
        subprocess.check_output(["git", "checkout", "-b", branch], cwd=path)


def remove_git_from_project(name: str):
    path: str = get_project_path(name)
    gitd = os.path.join(path, ".git")
    if os.path.exists(gitd):
        shutil.rmtree(gitd)


def add_layer_to_project(name: str, layer: str, content: dict):
    path: str = get_project_path(name)
    layer_fpath = os.path.join(path, "dtproject", f"{layer}.yaml")
    # add layer
    with open(layer_fpath, "w") as fout:
        yaml.safe_dump(content, fout)


def remove_layer_from_project(name: str, layer: str):
    path: str = get_project_path(name)
    layer_fpath = os.path.join(path, "dtproject", f"{layer}.yaml")
    # remove layer file
    os.remove(layer_fpath)


def readonly_filesystem() -> bool:
    stat = os.statvfs('/library/src')
    return bool(stat.f_flag & os.ST_RDONLY)


class git_repository(ContextDecorator):

    def __init__(self, name: str, remote: Optional[str] = None, branch: Optional[str] = None):
        self._name: str = name
        self._remote: Optional[str] = remote
        self._branch: Optional[str] = branch

    def __enter__(self):
        add_git_to_project(self._name, remote=self._remote, branch=self._branch)
        return self

    def __exit__(self, *exc):
        remove_git_from_project(self._name)
        return False


class custom_layer(ContextDecorator):

    def __init__(self, name: str, layer: str, content: Union[Dict[str, Any], Layer]):
        self._name: str = name
        self._layer: str = layer
        pd = get_project_path(name)
        # load current layer content from disk (if it exists)
        self._layer_fpath: str = os.path.join(pd, "dtproject", f"{layer}.yaml")
        self._old_content: Optional[bytes] = None
        if os.path.exists(self._layer_fpath):
            with open(self._layer_fpath, "rb") as fin:
                self._old_content = fin.read()
        # serialize new layer content
        if isinstance(content, DataClassLayer):
            self._new_content: Dict[str, Any] = dataclasses.asdict(content)
        elif isinstance(content, (DictLayer, dict)):
            self._new_content: Dict[str, Any] = content.copy()
        else:
            raise ValueError(f"Layer of type '{content.__class__}' not supported.")

    def __enter__(self):
        add_layer_to_project(self._name, self._layer, self._new_content)
        return self

    def __exit__(self, *exc):
        if self._old_content is None:
            # no old content, remove the layer file
            remove_layer_from_project(self._name, self._layer)
        else:
            # we have old content, restore layer
            with open(self._layer_fpath, "wb") as fout:
                fout.write(self._old_content)
        # ---
        return False


class base_layer(custom_layer):
    def __init__(self, name: str, layer: Union[Dict[str, Any], LayerBase]):
        super(base_layer, self).__init__(name, "base", layer)


class options_layer(custom_layer):
    def __init__(self, name: str, layer: Union[Dict[str, Any], LayerOptions]):
        super(options_layer, self).__init__(name, "options", layer)


class recipes_layer(custom_layer):
    def __init__(self, name: str, layer: Union[Dict[str, Any], LayerRecipes]):
        super(recipes_layer, self).__init__(name, "recipes", layer)


class value(ContextDecorator):
    """
    This context serves only the purpose of allowing a more readable grouping of statements
    For example:

        with value(5) as v:
            print(v)

        with value(7) as v:
            print(v)

    """
    def __init__(self, value: Any):
        self._value: Any = value

    def __enter__(self) -> Any:
        return self._value

    def __exit__(self, *exc):
        return False


def skip_if_code_mounted(fcn):
    return skipIf(readonly_filesystem(), "not adding GIT repository to mounted code")(fcn)
