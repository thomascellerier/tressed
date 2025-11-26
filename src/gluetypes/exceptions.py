__all__ = ["GluetypesError", "GluetypesTypeError", "GluetypesValueError"]


class GluetypesError(Exception):
    pass


class GluetypesTypeError(GluetypesError, TypeError):
    pass


class GluetypesValueError(GluetypesError, ValueError):
    pass
