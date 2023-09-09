import os.path
import shutil
import subprocess
from contextlib import ContextDecorator
from typing import Optional, Dict
from unittest import skipIf

import yaml

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

    def __init__(self, name: str, layer: str, content: Dict[str, object]):
        self._name: str = name
        self._layer: str = layer
        self._content: Dict[str, object] = content

    def __enter__(self):
        add_layer_to_project(self._name, self._layer, self._content)
        return self

    def __exit__(self, *exc):
        remove_layer_from_project(self._name, self._layer)
        return False


def skip_if_code_mounted(fcn):
    return skipIf(readonly_filesystem(), "not adding GIT repository to mounted code")(fcn)
