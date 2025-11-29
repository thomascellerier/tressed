__all__ = ["TressedError", "TressedTypeError", "TressedValueError"]


class TressedError(Exception):
    pass


class TressedTypeError(TressedError, TypeError):
    pass


class TressedValueError(TressedError, ValueError):
    pass
