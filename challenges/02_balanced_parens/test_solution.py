import pytest

from solution import is_balanced


@pytest.mark.parametrize("s", [
    "",
    "()",
    "[]",
    "{}",
    "()[]{}",
    "([{}])",
    "((()))",
    "{[()]}",
    "a(b[c]{d})e",
    "no brackets at all",
])
def test_balanced(s):
    assert is_balanced(s) is True


@pytest.mark.parametrize("s", [
    "(",
    ")",
    "(]",
    "([)]",
    "{[}]",
    "(()",
    "())",
    ")(",
    "[(])",
])
def test_unbalanced(s):
    assert is_balanced(s) is False


def test_returns_bool_not_truthy():
    # Tests that the function returns an actual bool, not 0/1/None/"".
    assert isinstance(is_balanced("()"), bool)
    assert isinstance(is_balanced("("), bool)
