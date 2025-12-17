import gc
import sys

from tressed.predicates import is_re_pattern_type


def test_is_re_pattern_type() -> None:
    # Make sure that the re import is lazy
    if "re" in sys.modules:
        del sys.modules["re"]
        gc.collect()

    assert is_re_pattern_type(int) is False
    assert is_re_pattern_type(str) is False

    assert "re" not in sys.modules

    import re

    assert is_re_pattern_type(re.Pattern) is True

    assert "re" in sys.modules
