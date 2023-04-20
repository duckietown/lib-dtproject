from typing import Dict, Callable, Tuple

ProjectType = str
ProjectTypeVersion = str
RelativePath = str
AbsolutePath = str
HostPath = str
ContainerPath = str
RepositoryName = str

REQUIRED_METADATA_KEYS = {
    "*": ["TYPE_VERSION"],
    "1": ["TYPE", "VERSION"],
    "2": ["TYPE", "VERSION"],
    "3": ["TYPE", "VERSION"],
    "4": ["TYPE", "VERSION"],
}

REQUIRED_METADATA_PER_TYPE_KEYS = {
    "template-exercise": {
        "3": ["NAME", "RECIPE_REPOSITORY", "RECIPE_BRANCH", "RECIPE_LOCATION"],
    },
}

CANONICAL_ARCH = {
    "arm": "arm32v7",
    "arm32v7": "arm32v7",
    "armv7l": "arm32v7",
    "armhf": "arm32v7",
    "x64": "amd64",
    "x86_64": "amd64",
    "amd64": "amd64",
    "Intel 64": "amd64",
    "arm64": "arm64v8",
    "arm64v8": "arm64v8",
    "armv8": "arm64v8",
    "aarch64": "arm64v8",
}

BUILD_COMPATIBILITY_MAP = {"arm32v7": ["arm32v7"], "arm64v8": ["arm32v7", "arm64v8"], "amd64": ["amd64"]}

DOCKER_LABEL_DOMAIN = "org.duckietown.label"

ARCH_TO_PLATFORM = {"arm32v7": "linux/arm/v7", "arm64v8": "linux/arm64", "amd64": "linux/amd64"}

ARCH_TO_PLATFORM_OS = {"arm32v7": "linux", "arm64v8": "linux", "amd64": "linux"}

ARCH_TO_PLATFORM_ARCH = {"arm32v7": "arm", "arm64v8": "arm64", "amd64": "amd64"}

ARCH_TO_PLATFORM_VARIANT = {"arm32v7": "v7", "arm64v8": "", "amd64": ""}

# kept for backward compatibility
DISTRO_KEY = {"1": "MAJOR", "2": "DISTRO", "3": "DISTRO"}

TEMPLATE_TO_SRC: Dict[ProjectType,
                      Dict[ProjectTypeVersion,
                           Callable[[RepositoryName], Tuple[RelativePath, ContainerPath]]]] = {
    # NOTE: these are not templates, they only serve the project matching their names
    "dt-commons": {
        "1": lambda _repo: ("code", "/packages/{:s}/".format(_repo)),
        "2": lambda _repo: ("", "/code/{:s}/".format(_repo)),
        "3": lambda _repo: ("", "/code/{:s}/".format(_repo)),
    },
    "dt-ros-commons": {
        "1": lambda _repo: ("", "/code/catkin_ws/src/{:s}/".format(_repo)),
        "2": lambda _repo: ("", "/code/catkin_ws/src/{:s}/".format(_repo)),
        "3": lambda _repo: ("", "/code/catkin_ws/src/{:s}/".format(_repo)),
    },
    # NOTE: these are templates and are shared by multiple projects
    "template-basic": {
        "1": lambda _repo: ("code", "/packages/{:s}/".format(_repo)),
        "2": lambda _repo: ("", "/code/{:s}/".format(_repo)),
        "3": lambda _repo: ("", "/code/{:s}/".format(_repo)),
        "4": lambda _repo: ("", "/code/{:s}/".format(_repo)),
    },
    "template-ros": {
        "1": lambda _repo: ("", "/code/catkin_ws/src/{:s}/".format(_repo)),
        "2": lambda _repo: ("", "/code/catkin_ws/src/{:s}/".format(_repo)),
        "3": lambda _repo: ("", "/code/catkin_ws/src/{:s}/".format(_repo)),
    },
    "template-core": {
        "1": lambda _repo: ("", "/code/catkin_ws/src/{:s}/".format(_repo)),
        "2": lambda _repo: ("", "/code/catkin_ws/src/{:s}/".format(_repo)),
        "3": lambda _repo: ("", "/code/catkin_ws/src/{:s}/".format(_repo)),
    },
    "template-exercise-recipe": {
        "3": lambda _repo: ("packages", "/code/catkin_ws/src/{:s}/packages".format(_repo))
    },
    "template-exercise": {
        "3": lambda _repo: ("packages/*", "/code/catkin_ws/src/{:s}/packages".format(_repo))
    },
}

TEMPLATE_TO_LAUNCHFILE: Dict[ProjectType,
                             Dict[ProjectTypeVersion,
                                  Callable[[RepositoryName], Tuple[RelativePath, ContainerPath]]]] = {
    # NOTE: these are not templates, they only serve the project matching their names
    "dt-commons": {
        "1": lambda _repo: ("launch.sh", "/launch/{:s}/launch.sh".format(_repo)),
        "2": lambda _repo: ("launchers", "/launch/{:s}".format(_repo)),
        "3": lambda _repo: ("launchers", "/launch/{:s}".format(_repo)),
    },
    "dt-ros-commons": {
        "1": lambda _repo: ("launch.sh", "/launch/{:s}/launch.sh".format(_repo)),
        "2": lambda _repo: ("launchers", "/launch/{:s}".format(_repo)),
        "3": lambda _repo: ("launchers", "/launch/{:s}".format(_repo)),
    },
    # NOTE: these are templates and are shared by multiple projects
    "template-basic": {
        "1": lambda _repo: ("launch.sh", "/launch/{:s}/launch.sh".format(_repo)),
        "2": lambda _repo: ("launchers", "/launch/{:s}".format(_repo)),
        "3": lambda _repo: ("launchers", "/launch/{:s}".format(_repo)),
        "4": lambda _repo: ("launchers", "/launch/{:s}".format(_repo)),
    },
    "template-ros": {
        "1": lambda _repo: ("launch.sh", "/launch/{:s}/launch.sh".format(_repo)),
        "2": lambda _repo: ("launchers", "/launch/{:s}".format(_repo)),
        "3": lambda _repo: ("launchers", "/launch/{:s}".format(_repo)),
    },
    "template-core": {
        "1": lambda _repo: ("launch.sh", "/launch/{:s}/launch.sh".format(_repo)),
        "2": lambda _repo: ("launchers", "/launch/{:s}".format(_repo)),
        "3": lambda _repo: ("launchers", "/launch/{:s}".format(_repo)),
    },
    "template-exercise-recipe": {"3": lambda _repo: ("launchers", "/launch/{:s}".format(_repo))},
    "template-exercise": {"3": lambda _repo: ("launchers", "/launch/{:s}".format(_repo))},
}

TEMPLATE_TO_ASSETS: Dict[ProjectType,
                         Dict[ProjectTypeVersion,
                              Callable[[RepositoryName], Tuple[RelativePath, ContainerPath]]]] = {
    "template-exercise-recipe": {
        "3": lambda _repo: ("assets/*", "/code/catkin_ws/src/{:s}/assets".format(_repo))
    },
    "template-exercise": {
        "3": lambda _repo: ("assets/*", "/code/catkin_ws/src/{:s}/assets".format(_repo))
    },
}

TEMPLATE_TO_DOCS: Dict[ProjectType,
                       Dict[ProjectTypeVersion, RelativePath]] = {
    # NOTE: these are not templates, they only serve the project matching their names
    "dt-commons": {
        # versions 1-3 are not supported by this library
        "4": "docs",
    },
    "dt-ros-commons": {
        # versions 1-3 are not supported by this library
        "4": "docs",
    },
    # NOTE: these are templates and are shared by multiple projects
    "template-basic": {
        # versions 1-3 are not supported by this library
        "4": "docs",
    },
    "template-ros": {
        # versions 1-3 are not supported by this library
        "4": "docs",
    },
    "template-library": {
        # version 1 is not supported by this library
        "2": "docs",
    },
    "template-book": {
        # version 1 is not supported by this library
        "2": "",
    }
}

DCSS_DOCKER_IMAGE_METADATA = "https://duckietown-public-storage.s3.amazonaws.com/docker/image/{registry}/" \
                             "{organization}/{repository}/{tag}/latest.json"
