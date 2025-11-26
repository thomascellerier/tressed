TYPE_CHECKING = False
if TYPE_CHECKING:
    from gluetypes.loader.types import TypePath

__all__ = [
    "specialize_load_tuple",
]


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

    code = """\
def __specialized_fn(value, loader):
"""
    match args:
        case []:
            pass
        case [arg]:
            code += """\
    item_0, = value
"""
        case [*args]:
            code += f"""\
    {", ".join(f"item_{pos}" for pos in range(len(args)))} = value
"""
    code += """\
    _load = loader._load
    return (
"""
    for pos, arg in enumerate(args):
        type_path_str = repr((*type_path, pos))
        if type(arg) is not type:
            # Failed specialization
            return None
        code += f"""\
        _load(item_{pos}, {arg.__qualname__}, {type_path_str}),
"""
    code += """\
    )

"""
    return code
