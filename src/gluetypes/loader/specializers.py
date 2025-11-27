TYPE_CHECKING = False
if TYPE_CHECKING:
    from typing import Final

    from gluetypes.loader.types import TypePath, TypeLoaderFn, TypePathItem

__all__ = [
    "specialize_load_tuple",
]


class Codegen:
    __slots__ = ("fn_name", "indent", "_lines", "_cached_code")

    def __init__(self, fn_name: str = "__specialized_fn") -> None:
        self.fn_name: Final = fn_name
        self.indent: Final = "    "

        self._lines = []
        self._cached_code: str | None = None

    def code(self) -> str:
        if cached_code := self._cached_code:
            return cached_code
        import io

        builder = io.StringIO()
        builder.write(f"def {self.fn_name}(value, loader):\n")
        for line in self._lines:
            builder.write(self.indent)
            builder.write(line)
            builder.write("\n")
        builder.write("\n")
        cached_code = builder.getvalue()

        self._cached_code = cached_code
        self._lines.clear()
        return cached_code

    def exec(self) -> TypeLoaderFn:
        # NOTE: This relies on the source being executed being only trusted and validated inputs.
        globals_ = {}
        locals_ = {}
        exec(self.code(), globals_, locals_)
        return locals_[self.fn_name]

    def _emit_line(self, line: str) -> None:
        self._lines.append(line)

    def emit_unpack(self, ident: str, arity: int) -> tuple[str, ...]:
        # TODO: Allocate identifiers!
        idents = tuple(f"_item_{pos}" for pos in range(arity))
        match arity:
            case 0:
                pass
            case 1:
                self._emit_line(f"{idents[0]}, = {ident}")
            case _:
                self._emit_line(f"{', '.join(idents)} = {ident}")
        return idents

    def emit_load_fn(self, ident: str = "_load") -> str:
        self._emit_line(f"{ident} = loader._load")
        return ident

    def emit_load(
        self,
        loader_ident: str,
        ident: str,
        type_form: type,
        type_path: TypePath,
        type_path_item: TypePathItem,
    ) -> str:
        # TODO: Allocate identifiers!
        loaded_ident = f"{ident}_loaded"
        type_path_str = repr((*type_path, type_path_item))
        # TODO: Handle type forms!
        self._emit_line(
            f"{loaded_ident} = _load({ident}, {type_form.__qualname__}, {type_path_str})"
        )
        return loaded_ident


def specialize_load_tuple[T](
    type_form: type[T],
    type_path: TypePath,
) -> str | None:
    """
    Generate specialized function for given type at given path.
    TODO: Specializer helper class based on ast + ast.unparse to generate code.
    """
    from gluetypes.predicates import get_args

    args = get_args(type_form)
    assert args is not None

    codegen = Codegen()
    # TODO: Change to emit_unpack_args, return tuple of (ident, type_form)
    items = codegen.emit_unpack("value", len(args))
    load_fn = codegen.emit_load_fn()
    loaded = []
    for pos, (item, arg_type_form) in enumerate(zip(items, args)):
        loaded.append(codegen.emit_load(load_fn, item, arg_type_form, type_path, pos))
    # TODO: Add codegen to return
    codegen._emit_line("return (")
    for loaded_item in loaded:
        codegen._emit_line(f"{codegen.indent}{loaded_item},")
    codegen._emit_line(")")
    return codegen.code()
