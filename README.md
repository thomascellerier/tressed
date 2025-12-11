<p align="center"><strong>tressed</strong> <em>- Deserialize and serialize types, in any order.</em></p>

<p align="center">
<a href="https://github.com/thomascellerier/tressed/actions/workflows/test.yaml">
    <image src="https://github.com/github/docs/actions/workflows/test.yml/badge.svg">
</a>
<a href="https://pypi.org/project/tressed/">
    <img src="https://badge.fury.io/py/tressed.svg" alt="Package version">
</a>
</p>

Tressed is a straightforwad pure python library to deserialize to and serialize from python types.

---

Add tressed to your project using uv:
```shell
uv add tressed
```

Or install using pip:
```shell
pip install tressed
```

Then just import tressed and get coding.
```Python
import tressed
```

Ok, let's get going!<br/>

For simple use cases, you can use the default loader and dumper directly:
```python
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
```python
>>> from dataclasses import dataclass, field
>>> import json
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
>>> raw_value = json.loads(
...     '{"someField": "foo", "OTHER": [2, "humbug"]}'
... )
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
>>> dumped = dumper.dump(value)
>>> pprint(dumped)
{'OTHER': [2, 'humbug'],
 'SomeDefaultFactoryField': [1, 2, 3],
 'SomeDefaultField': 'bar',
 'SomeField': 'foo'}

>>> print(repr(json.dumps(dumped)))
'{"SomeField": "foo", "SomeDefaultField": "bar", "SomeDefaultFactoryField": [1, 2, 3], "OTHER": [2, "humbug"]}'

>>> dumper = Dumper(hide_defaults=True, alias_field=None)
>>> print(json.dumps(dumper.dump(value)))
{"some_field": "foo", "other_field": [2, "humbug"]}

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

Tressed loaders and dumpers work by mapping type forms to handlers.<br/>
For example, by default a dataclass will be loaded by `tressed.loader.loaders.load_dataclass` and dumped by `tressed.dumper.dumpers.dump_dataclass`.

When loading or dumping a value, the loader or dumper first checks for an exact match in the type handlers.<br/>

If no exact match is found it iterates through the type mappers in order until a type predicate returns `True`.<br/>
A type mapper maps a type predicate function to a handler.<br/>

A type predicate is a function returning `True` if the type form matches the predicate.<br/>

For example:
```python
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

If a predicate matches the given type, the corresponding handler is used.<br>
Additionally it is added as an entry in the type handlers to enable a quick lookup the next time the same type form is encountered.<br/>

If a handler was found the handler is called on the given arguments.<br/>
If no handler was a found a `tressed.exception.TressedTypeError` is raised.<br/>

### Custom types

It is possible to load and dump custom types by using one or both of the `extra_type_handlers` and `extra_type_mappers`
arguments when instantiating a `Dumper` or `Loader`.
These handlers will be added to the default handlers.

For example, a loader with an additional type handler for a custom type:
```python
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
```python
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
```python
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
```python
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

### Aliases

Tressed loaders and dumpers have support for resolving aliases.<br/>
This enables easily supporting patterns like serializing to and from JSON using, e.g. camelCase or PascalCase.

Both dumpers and loaders use the same `tressed.alias.AliasResolver` class to resolve aliases.
The alias resolve combines an alias function of type `tressed.alias.AliasFn` with an alias cache.

The loader and dumper use the alias resolver to resolve a field name to an alias.
By default this is used for `dataclasses.dataclass` and `typing.NamedTuple`.
This mechanism can easily be used for custom types by calling `{Loader,Dumper}._resolve_alias`.

Generally alias resolution can map a field name directly to an alias.
To enable more powerful custom behavior alias functions also get passed the type form and type path.

For example `alias_resolver.resolve("some_field", SomeEnum, ("path", "to", "field"))` could be used
to upper case enum values but camelCase other fields, unless they are top-level:
```python
>>> from enum import IntEnum, auto
>>> from pprint import pprint
>>>
>>> from tressed import TypeForm, TypePath
>>> from tressed.alias import AliasResolver, to_camel
>>>
>>> class SomeEnum(IntEnum):
...     some_field = auto()
...     some_other_field = auto()
...
>>>
>>> def custom_alias_fn(name: str, type_form: TypeForm, type_path: TypePath) -> str:
...     if type_form is SomeEnum:
...         return name.upper()
...
...     if len(type_path) > 0:
...         return to_camel(name)
...
...     return name
>>>    
>>> alias_resolver = AliasResolver(alias_fn=custom_alias_fn)
>>>
>>> pprint(alias_resolver.resolve("some_field", SomeEnum, ("path", "to", "field")))
'SOME_FIELD'
>>> pprint(alias_resolver.resolve("some_field", int, ("path", "to", "field")))
'someField'
>>> pprint(alias_resolver.resolve("some_field", int, ()))
'some_field'

```

The `type_form`and `type_path` parameters are optional, the `AliasResolver` normalizes alias functions to the
3 parameter form by wrapping them in a function discarding any unused arguments.

By default the alias resolve caches the result of the alias resolution for the given arguments.
This is to avoid repeatidly doing expensive type introspection.
This behavior can be disabled by passing `cache_resolved_aliases=False` when instantiating the alias resolver.

#### Built-in alias functions

A few commonly used alias functions are provided by tressed as part of the `tressed.alias` module:
- `to_camel`: Convert field name to camelCase.
- `to_pascal`: Convert field name to PascalCase.
- `to_identity`: Use field name as is, the default behavior.

#### Composing alias functions

An alias resolve accepts a single alias function.
Several alias functions can be composed into a single alias function to enable more advanced behavior.

The built-in `tressed.alias.compose_alias_fn` allows composing several alias functions together, returning
a single alias functio suitable as an argument to an `AliasResolver`.

It accepts a variadic number of optional alias functions, that is functions returning an alias or `None`.
If a function returns an alias it is used as is, else the next alias function is tried.
Finally if no optional alias function matches, the default alias function is used, by default `to_identity`.

For example:
```python
>>> from pprint import pprint
>>> from tressed.alias import compose_alias_fn
>>>
>>> def maybe_to_upper(name: str) -> str | None:
...     if name.casefold().startswith("foo"):
...         return name.upper()
...     return None
...
>>> def maybe_to_lower(name: str) -> str | None:
...     if name.casefold().startswith("bar"):
...         return name.lower()
...     return None
...
>>> def to_underscores(name: str) -> str:
...     return "_"*len(name)
...
>>> alias_fn = compose_alias_fn(maybe_to_upper, maybe_to_lower, default_alias_fn=to_underscores)
>>>
>>> pprint(alias_fn("FooBar", str, ()))
'FOOBAR'

>>> pprint(alias_fn("BarBar", str, ()))
'barbar'

>>> pprint(alias_fn("Baz", str, ()))
'___'

```

This mechanism is used by the loader and dumper to combine a dataclass field alias function, allowing per field
aliases with a user provided alias function like `to_camel`. By default it uses `alias_field="alias"`.<br/>
This can be disabled by passing `alias_field=None` when instantiating a loader or dumper.

For example:
```python
>>> from dataclasses import dataclass, field
>>> from pprint import pprint
>>>
>>> from tressed import Dumper
>>>
>>> @dataclass
... class SomeClass:
...     some_field: int = field(
...         metadata={
...             "alias": "SomeField",
...             "name": "someField"
...         }
...     )
...     other_field: str
...
>>> some_value = SomeClass(123, "foo")
>>>
>>> dumper = Dumper(alias_fn=str.upper)
>>> pprint(dumper.dump(some_value), sort_dicts=False)
{'SomeField': 123, 'OTHER_FIELD': 'foo'}
>>>
>>> dumper = Dumper(alias_field="name")
>>> pprint(dumper.dump(some_value), sort_dicts=False)
{'someField': 123, 'other_field': 'foo'}
>>>
>>> dumper = Dumper(alias_field="name", alias_fn=str.upper)
>>> pprint(dumper.dump(some_value), sort_dicts=False)
{'someField': 123, 'OTHER_FIELD': 'foo'}
>>>
>>> dumper = Dumper(alias_field=None, alias_fn=str.upper)
>>> pprint(dumper.dump(some_value), sort_dicts=False)
{'SOME_FIELD': 123, 'OTHER_FIELD': 'foo'}

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
