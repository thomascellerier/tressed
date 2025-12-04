__all__ = [
    "TypePathItem",
    "TypePath",
]

type TypePathItem = str | int
type TypePath = tuple[TypePathItem, ...]
