__all__ = [
    "TypePathItem",
    "TypePath",
    "type_path_repr",
]

type TypePathItem = str | int
type TypePath = tuple[TypePathItem, ...]


def type_path_repr(type_path: TypePath) -> str:
    return f".{'.'.join(map(str, type_path))}"
