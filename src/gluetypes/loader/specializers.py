TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import Final

    from gluetypes.loader.types import TypePath, TypeLoaderFn, TypePathItem

__all__ = [
    "specialize_load_tuple",
    "specialize_load_simple_collection",
]


class Codegen:
    __slots__ = ("fn_name", "indent", "_parts", "_cached_code")

    def __init__(self, fn_name: str = "__specialized_fn") -> None:
        self.fn_name: Final = fn_name
        self.indent: Final = "    "

        self._parts = []
        self._cached_code: str | None = None

    def code(self) -> str:
        if cached_code := self._cached_code:
            return cached_code
        import io

        builder = io.StringIO()
        builder.write(f"def {self.fn_name}(value, loader):\n")
        for line in self._parts:
            builder.write(line)
        builder.write("\n")
        cached_code = builder.getvalue()

        self._cached_code = cached_code
        self._parts.clear()
        return cached_code

    def exec(self) -> TypeLoaderFn:
        # NOTE: This relies on the source being executed being only trusted and validated inputs.
        globals_ = {}
        locals_ = {}
        exec(self.code(), globals_, locals_)
        return locals_[self.fn_name]

    def _emit(self, part: str) -> None:
        self._parts.append(part)

    def _emit_indent(self, indent: int = 0) -> None:
        self._emit(self.indent * (indent + 1))

    def _emit_newline(self) -> None:
        self._emit("\n")

    def _emit_line(self, line: str, indent: int = 0) -> None:
        self._emit_indent(indent)
        self._emit(line)
        self._emit_newline()

    def emit_unpack_args(
        self, ident: str, args: tuple[type, ...]
    ) -> tuple[tuple[str, type], ...]:
        # TODO: Allocate identifiers!
        items = tuple((f"_item_{pos}", type_form) for pos, type_form in enumerate(args))
        match items:
            case []:
                pass
            case [(item_ident, _)]:
                self._emit_line(f"{item_ident}, = {ident}")
            case [*_]:
                self._emit_line(
                    f"{', '.join(item_ident for item_ident, _ in items)} = {ident}"
                )
        return items

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

    def emit_tuple(self, idents: Iterable[str], *, compact: bool = False) -> None:
        self._emit("(")
        if not compact:
            self._emit_newline()
        for ident in idents:
            if not compact:
                self._emit_indent(indent=1)
            self._emit(f"{ident},")
            if not compact:
                self._emit_newline()
        if not compact:
            self._emit_indent()
        self._emit(")")
        self._emit_newline()

    def emit_return(self) -> None:
        self._emit_indent()
        self._emit("return ")


def specialize_load_tuple[T](
    type_form: type[T],
    type_path: TypePath,
) -> str | None:
    """
    Generate specialized function for given type at given path.
    """
    from gluetypes.predicates import get_args

    args = get_args(type_form)
    assert args is not None

    codegen = Codegen()
    items = codegen.emit_unpack_args("value", args)
    load_fn = codegen.emit_load_fn()
    loaded = []
    for pos, (item, arg_type_form) in enumerate(items):
        loaded.append(codegen.emit_load(load_fn, item, arg_type_form, type_path, pos))
    codegen.emit_return()
    codegen.emit_tuple(loaded)
    return codegen.code()


def specialize_load_simple_collection[T](
    type_form: type[T],
    type_path: TypePath,
) -> str | None:
    """
    Generate specialized function for given type at given path.
    """
    from gluetypes.predicates import get_args, get_origin

    origin = get_origin(type_form)
    assert origin is not None

    args = get_args(type_form)
    assert args is not None
    arg_type_form = args[0]

    codegen = Codegen()

    load_fn = codegen.emit_load_fn()
    codegen.emit_return()
    if origin is list:
        open, close = "[", "]"
    elif origin is set:
        open, close = "{", "}"
    elif origin is frozenset:
        open, close = "({", "})"
    else:
        open, close = f"{origin.__qualname__}([", "])"

    type_path_str = f"({', '.join(item for item in (*map(repr, type_path), 'pos'))})"
    codegen._emit(f"""{open}
        {load_fn}(item, {arg_type_form.__qualname__}, {type_path_str})
        for pos, item
        in enumerate(value)
    {close}
""")
    return codegen.code()
