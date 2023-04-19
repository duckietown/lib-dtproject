import yaml


def parse_configurations(config_file: str) -> dict:
    with open(config_file, "rt") as fin:
        configurations_content = yaml.load(fin, Loader=yaml.SafeLoader)
    if "version" not in configurations_content:
        raise ValueError("The configurations file must have a root key 'version'.")
    if configurations_content["version"] == "1.0":
        return configurations_content["configurations"]
