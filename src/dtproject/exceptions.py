__all__ = [
    "DTProjectError",
    "RecipeProjectNotFound",
    "DTProjectNotFound",
    "MalformedDTProject",
    "InconsistentDTProject",
    "UnsupportedDTProjectVersion",
    "NotFound",
]


class DTProjectError(RuntimeError):
    pass


class RecipeProjectNotFound(DTProjectError):
    pass


class DTProjectNotFound(DTProjectError):
    pass


class MalformedDTProject(DTProjectError):
    pass


class InconsistentDTProject(DTProjectError):
    pass


class UnsupportedDTProjectVersion(DTProjectError):
    pass


class NotFound(DTProjectError):
    pass
