<p align="center"><strong>tressed</strong> <em>- Deserialize and serialize types, in any order.</em></p>

<p align="center">
<a href="https://github.com/thomascellerier/tressed/actions/workflows/test.yaml">
    <image src="https://github.com/github/docs/actions/workflows/test.yml/badge.svg">
</a>
<a href="https://pypi.org/project/tressed/">
    <img src="https://badge.fury.io/py/tressed.svg" alt="Package version">
</a>
</p>

Tressed is a easy to use pure python library to deserialize and serialize to and from Python types.

---

Install tressed using pip:

```shell
$ pip install tressed
```

Now, let's get started:

```pycon
>>> from dataclasses import dataclass, field
>>> from pprint import pprint
>>> 
>>> from tressed.loader import Loader
>>> from tressed.alias import to_camel
>>> 
>>> @dataclass
... class SomeDataclass:
...     some_field: str
...     some_default_field: str = "bar"
...     some_default_factory_field: list[int] = field(default_factory=lambda: [1, 2, 3])
...     other_field: tuple[int, str] = field(metadata={"alias": "OTHER"}, kw_only=True)
...     
>>> value = {
...     "someField": "foo",
...     "OTHER": (2, "humbug"),
... }
... 
>>> loader = Loader(alias_fn=to_camel)
>>> pprint(loader.load(value, SomeDataclass))
SomeDataclass(some_field='foo',
              some_default_field='bar',
              some_default_factory_field=[1, 2, 3],
              other_field=(2, 'humbug'))
```

## Features
### Supported type forms

The following type forms are supported out of the box:

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

### Supported source types

Data can be loaded from the following basic types, matching types used by
common serialization formats.

Additionally data can be loaded from argparse namespaces to support
easily loading arguments into data types for simple CLI applications.

- int
- float
- bool
- str
- list
- dict
- argparse.Namespace

## Installation

Using pip:

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
