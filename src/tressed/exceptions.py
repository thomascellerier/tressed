__all__ = [
    "TressedError",
    "TressedTypeError",
    "TressedValueError",
    "TressedValueErrorGroup",
]


class TressedError(Exception):
    pass


class TressedTypeError(TressedError, TypeError):
    pass


class TressedValueError(TressedError, ValueError):
    pass


class TressedValueErrorGroup(ExceptionGroup[TressedValueError], TressedValueError):
    pass
