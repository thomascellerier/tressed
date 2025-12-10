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

Now we can get going!<br/>
For simple usecases, you can use the default loader and dumper directly:
```pycon
>>> from tressed import load, dump
>>> from pprint import pprint
>>>
>>>
>>> value = load([1, [2, 2], [3, 4]], tuple[int, set[float], complex])
>>> pprint(value)
(1, {2.0}, (3+4j))
>>>
>>> pprint(dump(value))
[1, [2.0], [3.0, 4.0]]

```

For more advanced use cases instantiate a Loader and/or a Dumper:
```pycon
>>> from dataclasses import dataclass, field
>>> from pprint import pprint
>>> 
>>> from tressed import Loader
>>> from tressed.alias import to_camel
>>> 
>>> @dataclass
... class SomeDataclass:
...     some_field: str
...     some_default_field: str = "bar"
...     some_default_factory_field: list[int] = field(default_factory=lambda: [1, 2, 3])
...     other_field: tuple[int, str] = field(metadata={"alias": "OTHER"}, kw_only=True)
...     
>>> raw_value = {
...     "someField": "foo",
...     "OTHER": (2, "humbug"),
... }
... 
>>> loader = Loader(alias_fn=to_camel)
>>> value = loader.load(raw_value, SomeDataclass)
>>> pprint(value)
SomeDataclass(some_field='foo',
              some_default_field='bar',
              some_default_factory_field=[1, 2, 3],
              other_field=(2, 'humbug'))

>>>
>>> from tressed import Dumper
>>> from tressed.alias import to_pascal
>>>
>>> dumper = Dumper(alias_fn=to_pascal)
>>> pprint(dumper.dump(value))
{'OTHER': [2, 'humbug'],
 'SomeDefaultFactoryField': [1, 2, 3],
 'SomeDefaultField': 'bar',
 'SomeField': 'foo'}

```

## Features

### Supported type forms

Tressed uses the proposed [PEP 747](https://peps.python.org/pep-0747/) `TypeForm` combined with [mypy 1.19](https://mypy.readthedocs.io/en/stable/changelog.html#pep-747-annotating-type-forms) to provide accurate types for the `Loader.load` function.

The following type forms are supported out of the box:

- `bool`
- `int`
- `float`
- `str`
- `complex`
- `tuple[T1, ..., Tn]`, `typing.Tuple[T1, ..., Tn]`
- `tuple[T, ...]`, `typing.Tuple[T, ...]` (a.k.a homogeneous tuple)
- `typing.NamedTuple`
- `list[T]`, `typing.List[T]`
- `set[T]`, `typing.Set[T]`
- `frozenset[T]`, `typing.FrozenSet[T]`
- `dict[K, V]`, `typing.Dict[K, V]`
- `typing.Literal[L1, .., Ln]`
- `typing.TypeAliasType`
- `T | None`, `typing.Optional[T]`
- `T1 | .. | Tn`, `typing.Union[T1, .., Tn]` (Untagged Union)
- `Annotated[T1 | ... | Tn, Discriminator(...)]` (Discriminated Union)
- `enum.Enum`
- `typing.TypedDict`, `typing_extensions.TypedDict` (including support for PEP 728 `closed` and `extra_items`)
- `dataclasses.dataclass`
- `typing.NewType[T]`
- `ipaddress.{IPv4Address, IPv6Address, IPv4Interface, IPv6Interface, IPv4Network, IPv6Network}`
- `uuid.UUID`
- `pathlib.Path`
- `datetime.{date,datetime,time}` (ISO 8601 format, using `datetime.{date,datetime,time}.fromisoformat`)

It is easy to add support for custom types as needed when creating a loader.

### Supported source types

Data can be loaded from the following basic types, matching types used by
common serialization formats.

Additionally data can be loaded from argparse namespaces to support
easily loading arguments into data types for simple CLI applications.

- `int`
- `float`
- `bool`
- `str`
- `list`
- `dict`
- `argparse.Namespace`

### Type handlers and type mappers

A type handler maps an exact type form to a handler.<br/>
A type mapper maps a type predicate function to a handler. A type predicate is a function returning True if the
type_form matches the predicate.<br/>
For example:
```pycon
>>> from pprint import pprint
>>> from tressed.predicates import is_generic_list_type
>>>
>>> pprint(is_generic_list_type(list[int]))
True

>>> pprint(is_generic_list_type(list[str]))
True

>>> pprint(is_generic_list_type(list))
False

>>> pprint(is_generic_list_type(set[int]))
False

```

When loading or dumping a value, the loader or dumper first checks for an exact match in the type handlers.<br/>
If no exact match is found it iterates through the type mappers in order until a type predicate returns True.<br/>
In that case an entry is added for this type form to the type handlers.<br/>

If a handler was found the handler is called on the given arguments.<br/>
If no handler was a found a `tressed.exception.TressedTypeError` is raised.<br/>

### Custom types

It is possible to load and dump custom types by using one or both of the `extra_type_handlers` and `extra_type_mappers`
arguments when instantiating a `Dumper` or `Loader`.
These handlers will be added to the default handlers.

For example, a loader with an additional type handler for a custom type:
```
>>> from pprint import pprint
>>>
>>> from tressed.loader import Loader
>>>
>>> class DoubleValue:
...     def __init__(self, value: int) -> None:
...         self.value = value * 2
...
...     def __repr__(self) -> str:
...         return str(self.value)
...
>>>
>>> loader = Loader(
...     extra_type_handlers={
...         DoubleValue: lambda value, type_form, type_path, loader: DoubleValue(value)
...     }
... )
>>>
>>> pprint(loader.load(21, DoubleValue))
42

```

Another example, a dumper with an additional type mapper for a custom type:
```
>>> from pprint import pprint
>>>
>>> from tressed import Dumper, TypeForm
>>>
>>> class ClassA:
...     def __str__(self) -> str:
...         return f"This is {self.__class__.__name__}"
...
>>> class ClassB(ClassA):
...     pass
...
>>>
>>> def is_class_a_type(type_form: TypeForm) -> bool:
...     return isinstance(type_form, type) and issubclass(type_form, ClassA)
...
>>> dumper = Dumper(
...     extra_type_mappers={
...         is_class_a_type: lambda value, type_path, dumper: str(value)
...     }
... )
...
>>> pprint(dumper.dump((ClassA(), ClassB())))
['This is ClassA', 'This is ClassB']

```

#### Bare-bones loader and dumper

Tressed supports setting up "bare-bones" loader and dumper without the default type handlers and type mappers.<br/>
To do that pass an empty dictionary for `default_type_mappers` and `default_type_handlers`.

For example, we define loader only supporting exactly a single type alias called `UpperStr` loading
string into their uppercase version:
```pycon
>>> from pprint import pprint
>>>
>>> from tressed import Loader
>>> from tressed.exceptions import TressedTypeFormError
>>>
>>> type UpperStr = str
>>>
>>> loader = Loader(
...     default_type_handlers={
...         UpperStr: lambda value, type_form, type_path, loader: value.upper()
...     },
...     default_type_mappers={},
... )
...
>>>
>>> pprint(loader.load("foo", UpperStr))
'FOO'

>>> try:
...     loader.load("foo", str)
... except TressedTypeFormError as e:
...     print(e)
...
Unhandled type form str at path . for value 'foo'

```

And a dumper only serializing a custom `Password` type to a string containing only `*` characters:
```pycon
>>> from pprint import pprint
>>>
>>> from tressed import Dumper, TypeForm
>>>
>>> class Password:
...     def __init__(self, value: str) -> None:
...         self.value = value
...
>>>
>>> def is_password_type(type_form: TypeForm) -> bool:
...     return isinstance(type_form, type) and issubclass(type_form, Password)
...
>>>
>>> dumper = Dumper(
...     default_type_handlers={},
...     default_type_mappers={
...         is_password_type: lambda password, type_path, dumper: "*" * len(password.value)
...     },
... )
...
>>>
>>> pprint(dumper.dump(Password("foobar")))
'******'

```

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
