import os
import re
import subprocess
from typing import List

from ..constants import DOCKER_LABEL_DOMAIN, CANONICAL_ARCH


def run_cmd(cmd):
    cmd = " ".join(cmd)
    return [line for line in subprocess.check_output(cmd, shell=True).decode("utf-8").split("\n") if line]


def dtlabel(key, value=None):
    label = f"{DOCKER_LABEL_DOMAIN}.{key.lstrip('.')}"
    if value is not None:
        label = f"{label}={value}"
    return label


def git_remote_url_to_https(remote_url):
    ssh_pattern = "git@([^:]+):([^/]+)/(.+)"
    res = re.search(ssh_pattern, remote_url, re.IGNORECASE)
    if res:
        return f"https://{res.group(1)}/{res.group(2)}/{res.group(3)}"
    return remote_url


def assert_canonical_arch(arch):
    if arch not in CANONICAL_ARCH.values():
        raise ValueError(
            f"Given architecture {arch} is not supported. "
            f"Valid choices are: {', '.join(list(set(CANONICAL_ARCH.values())))}"
        )


def canonical_arch(arch):
    if arch not in CANONICAL_ARCH:
        raise ValueError(
            f"Given architecture {arch} is not supported. "
            f"Valid choices are: {', '.join(list(set(CANONICAL_ARCH.values())))}"
        )
    # ---
    return CANONICAL_ARCH[arch]


def DEPRECATED(fcn):
    """This is a decorator that does nothing, it is just used to label functions that are deprecated"""
    return fcn


def load_dependencies_file(fpath: str, comments: bool = False) -> List[str]:
    # no deps file => no deps
    if not os.path.exists(fpath):
        return []
    # load deps
    with open(fpath, "rt") as fin:
        deps: List[str] = fin.readlines()
    # remove new line chars
    deps = list(map(lambda s: s.strip(), deps))
    # filter deps from comments
    if not comments:
        # remove empty lines
        deps = list(filter(lambda s: len(s.strip()) > 0, deps))
        # remove comments
        deps = list(filter(lambda s: not s.strip().startswith("#"), deps))
    # ---
    return deps
