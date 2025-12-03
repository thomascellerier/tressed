# tressed

Serialize and deserialize types, in any order.

## Usage

```Python
from dataclasses import dataclass, field
from tressed.loader import Loader

@dataclass
class SomeDataclass:
    foo: str
    bar: str = "bar"
    baz: list[int] = field(default_factory=lambda: [1, 2, 3])
    bar_bar: tuple[int, str] = field(metadata={"alias": "barBar"}, kw_only=True)

value = {
    "foo": "foo",
    "barBar": (2, "humbug"),
}

loader = Loader()
loaded = loader.load(value, SomeDataclass)

assert loaded == SomeDataclass(
    foo="foo",
    bar="bar",
    baz=[1, 2, 3],
    bar_bar=(2, "humbug"),
)
```

## Supported types

The following types are supported out of the box:

- bool
- int
- float
- str
- complex
- tuple[T1, ..., Tn], typing.Tuple[T1, ..., Tn]
- tuple[T, ...], typing.Tuple[T, ...] a.k.a homogeneous tuple
- typing.NamedTuple
- list[T], typing.List[T]
- set[T], typing.Set[T]
- frozenset[T], typing.FrozenSet[T]
- dict[K, V], typing.Dict[K, V]
- typing.TypedDict, typing\_extensions.TypedDict, including support for PEP 728 closed and extra\_items.
- dataclasses.dataclass
- typing.NewType[T]
- ipaddress.{IPv4Address,IPv6Address,IPv4Interface,IPv6Interface,IPv4Network,IPv6Network}

It is easy to add support for custom types as needed when creating a loader.

## Installation

Using pip:
```bash
pip install tressed
```

Or using uv:
```bash
uv add tressed
```

Then just import tressed and get coding.
```Python
import tressed
```

## Goals

- Provide easy serialization and deserialization to and from built-in and standard library types.
- Provide easy way to add support for custom types.
- Provide easy yet powerful support for serializaiton and deserialization aliases.
- Pure python, no additional runtime dependencies beyond the standard library.
- Do as little work as possible to be suitable for CLIs, for example using lazy imports as much as possible.

### Stretch goals
- Add first class support for concurrent loading and dumping, with support for asyncio and threading, for example deserializing a list of M objects on N threads.
- Use code generation internally similarly to dataclasses. Instead of doing metaprogramming each time, generate an actual function for the type that does (de)serialization. Interpret the first time, compile the second, using source or ast module, and then reuse the compiled function.
