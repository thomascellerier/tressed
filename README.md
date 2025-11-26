# gluetypes

Glue types together.

## Installation

Using pip:
```bash
pip install gluetypes
```

Or using uv:
```bash
uv add gluetypes
```

Then just import gluetypes and get coding.
```Python
import gluetypes
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
