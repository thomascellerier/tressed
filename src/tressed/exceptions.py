TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any, NoReturn

    from tressed.type_form import TypeForm
    from tressed.type_path import TypePath

__all__ = [
    "TressedError",
    "TressedTypeError",
    "TressedTypeFormError",
    "TressedValueError",
]


class TressedError(Exception):
    pass


class TressedTypeError(TressedError, TypeError):
    def __init__(
        self,
        value: Any,
        type_path: TypePath,
        message: str = "",
    ) -> None:
        self.value = value
        self.type = type(value)
        self.type_path = type_path
        self.message = message
        super(TypeError, self).__init__(self.type)

    def __str__(self) -> str:
        from tressed.type_form import type_form_repr
        from tressed.type_path import type_path_repr

        return (
            f"Unhandled type {type_form_repr(self.type)} "
            f"at path {type_path_repr(self.type_path)} "
            f"for value {self.value!r}{f': {self.message}' if self.message else ''}"
        )


class TressedTypeFormError(TressedError, TypeError):
    def __init__(
        self, value: Any, type_form: TypeForm, type_path: TypePath, message: str = ""
    ) -> None:
        self.value = value
        self.type_form = type_form
        self.type_path = type_path
        self.message = message
        super(TypeError, self).__init__(type_form)

    def __str__(self) -> str:
        from tressed.type_form import type_form_repr
        from tressed.type_path import type_path_repr

        return (
            f"Unhandled type form {type_form_repr(self.type_form)} "
            f"at path {type_path_repr(self.type_path)} "
            f"for value {self.value!r}{f': {self.message}' if self.message else ''}"
        )


class TressedValueError(TressedError, ValueError):
    def __init__(
        self,
        value: Any,
        type_form: TypeForm,
        type_path: TypePath,
        message: str = "",
        exceptions: Sequence[TressedValueError] = (),
    ) -> None:
        self.value = value
        self.type_form = type_form
        self.type_path = type_path
        self.message = message
        self.exceptions = exceptions
        super(ValueError, self).__init__(value)

    def __str__(self) -> str:
        from tressed.type_form import type_form_repr
        from tressed.type_path import type_path_repr

        value = (
            f"Failed to load value of type {type_form_repr(type(self.value))} "
            f"at path {type_path_repr(self.type_path)} "
            f"into type form {type_form_repr(self.type_form)}"
        )
        if self.message:
            value += f": {self.message}"
        if self.exceptions:
            value += f" ({len(self.exceptions)} sub-exceptions)"
        return value

    def raise_exception_group(self) -> NoReturn:
        """
        Raise as exception group.
        """
        raise ExceptionGroup(
            str(self),
            self.exceptions,
        )
