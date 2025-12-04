from tressed.alias import AliasResolver, to_camel, to_pascal


def test_to_camel() -> None:
    assert to_camel("foo_bar") == "fooBar"
    assert to_camel("foo") == "foo"
    assert to_camel("_foo") == "_foo"
    assert to_camel("_foO_bar__baz___") == "_fooBar__Baz___"
    assert to_camel("") == ""
    assert to_camel("_") == "_"
    assert to_camel("___") == "___"


def test_to_pascal() -> None:
    assert to_pascal("foo_bar") == "FooBar"
    assert to_pascal("foo") == "Foo"
    assert to_pascal("_foo") == "_Foo"
    assert to_pascal("_foO_bar__baz___") == "_FooBar__Baz___"
    assert to_pascal("") == ""
    assert to_pascal("_") == "_"
    assert to_pascal("___") == "___"


def test_alias_resolver() -> None:
    # Simple alias
    alias_resolver = AliasResolver(alias_fn=lambda s: s.upper())
    assert alias_resolver.resolve("FooBar", int, ()) == "FOOBAR"

    # Type form alias
    alias_resolver = AliasResolver(
        alias_fn=lambda s, t: s.upper() if t is int else s.lower()
    )
    assert alias_resolver.resolve("FooBar", int, ()) == "FOOBAR"
    assert alias_resolver.resolve("FooBar", str, ()) == "foobar"

    # Type path alias
    alias_resolver = AliasResolver(alias_fn=lambda s, _, p: "/".join(map(str, (*p, s))))
    assert (
        alias_resolver.resolve("FooBar", int, ("foo", 1, "bar")) == "foo/1/bar/FooBar"
    )
    assert alias_resolver.resolve("FooBar", str, ()) == "FooBar"


def test_alias_resolver_caching_enabled() -> None:
    count = 0

    def count_alias(_: str) -> str:
        nonlocal count
        count += 1
        return str(count)

    alias_resolver = AliasResolver(alias_fn=count_alias, cache_resolved_aliases=True)
    assert alias_resolver.resolve("foo", int, ("abc", 1)) == "1"
    assert alias_resolver.resolve("foo", int, ("abc", 1)) == "1"
    assert alias_resolver.resolve("foo", str, ("abc", 1)) == "2"
    assert alias_resolver.resolve("foo", str, ("abc", 1)) == "2"
    assert alias_resolver.resolve("foo", str, ("abc", 2)) == "3"
    assert alias_resolver.resolve("foo", str, ("abc", 2)) == "3"


def test_alias_resolver_caching_disabled() -> None:
    count = 0

    def count_alias(_: str) -> str:
        nonlocal count
        count += 1
        return str(count)

    alias_resolver = AliasResolver(alias_fn=count_alias, cache_resolved_aliases=False)

    assert alias_resolver.resolve("foo", int, ("abc", 1)) == "1"
    assert alias_resolver.resolve("foo", int, ("abc", 1)) == "2"
    assert alias_resolver.resolve("foo", str, ("abc", 1)) == "3"
    assert alias_resolver.resolve("foo", str, ("abc", 1)) == "4"
    assert alias_resolver.resolve("foo", str, ("abc", 2)) == "5"
    assert alias_resolver.resolve("foo", str, ("abc", 2)) == "6"
