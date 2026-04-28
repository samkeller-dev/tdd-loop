import pytest

from solution import from_roman, to_roman


@pytest.mark.parametrize("n, s", [
    (1,    "I"),
    (3,    "III"),
    (4,    "IV"),
    (9,    "IX"),
    (40,   "XL"),
    (58,   "LVIII"),
    (90,   "XC"),
    (400,  "CD"),
    (900,  "CM"),
    (1994, "MCMXCIV"),
    (3999, "MMMCMXCIX"),
])
def test_to_roman(n, s):
    assert to_roman(n) == s


@pytest.mark.parametrize("s, n", [
    ("I",        1),
    ("III",      3),
    ("IV",       4),
    ("IX",       9),
    ("XL",       40),
    ("LVIII",    58),
    ("XC",       90),
    ("CD",       400),
    ("CM",       900),
    ("MCMXCIV",  1994),
    ("MMMCMXCIX",3999),
])
def test_from_roman(s, n):
    assert from_roman(s) == n


@pytest.mark.parametrize("n", [1, 4, 9, 40, 58, 100, 444, 999, 1994, 2024, 3999])
def test_roundtrip(n):
    assert from_roman(to_roman(n)) == n
