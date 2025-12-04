__all__ = [
    "TressedError",
    "TressedTypeError",
    "TressedValueError",
    "TressedExceptionGroup",
]


class TressedError(Exception):
    pass


class TressedTypeError(TressedError, TypeError):
    pass


class TressedValueError(TressedError, ValueError):
    pass


class TressedExceptionGroup(ExceptionGroup, TressedError):
    pass
