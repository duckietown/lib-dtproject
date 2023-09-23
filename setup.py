from setuptools import find_packages, setup

# :==> Fill in your project data here
# The package name is the name on PyPI
# it is not the python module names.
package_name = "dtproject"
library_webpage = "http://github.com/duckietown/lib-dtproject"
maintainer = "Andrea F. Daniele"
maintainer_email = "afdaniele@duckietown.com"
short_description = "Utility library for working with Duckietown (DT)Projects"
full_description = f"""
{short_description}
"""


# Read version from the __init__ file
def get_version_from_source(filename):
    import ast

    vers = None
    with open(filename) as f:
        for line in f:
            if line.startswith("__version__"):
                # noinspection PyUnresolvedReferences
                vers = ast.parse(line).body[0].value.s
                break
        else:
            raise ValueError("No version found in %r." % filename)
    if vers is None:
        raise ValueError(filename)
    return vers


version = get_version_from_source("src/dtproject/__init__.py")

install_requires = [
    # add library dependencies here
    "pyyaml<=6.0.1",
    "dockertown<=0.2.3",
    "requests<=2.31.0",
    "dataclass-wizard<=0.22.2",
    "requirements-parser<=0.5.0"
]
tests_require = [
    # add testing requirements here
]

# compile description
underline = "=" * (len(package_name) + len(short_description) + 2)
description = """
{name}: {short}
{underline}

{long}
""".format(
    name=package_name,
    short=short_description,
    long=full_description,
    underline=underline,
)

# setup package
setup(
    name=package_name,
    author=maintainer,
    author_email=maintainer_email,
    url=library_webpage,
    tests_require=tests_require,
    install_requires=install_requires,
    package_dir={"": "src"},
    packages=find_packages("./src"),
    long_description=description,
    version=version,
)
