# Roman Numerals

Implement two pure functions in `solution.py`:

```python
def to_roman(n: int) -> str: ...
def from_roman(s: str) -> int: ...
```

`to_roman(n)` converts an integer in `[1, 3999]` to its standard Roman numeral
representation using subtractive notation. `from_roman(s)` is the inverse:
given a valid Roman numeral string in that range, return the integer.

## Subtractive notation

The six subtractive forms must be used where applicable:

| value | form |
|-------|------|
| 4     | IV   |
| 9     | IX   |
| 40    | XL   |
| 90    | XC   |
| 400   | CD   |
| 900   | CM   |

So `to_roman(1994) == "MCMXCIV"`, not `"MDCCCCLXXXXIIII"`.

## Examples

```python
to_roman(1)    == "I"
to_roman(4)    == "IV"
to_roman(9)    == "IX"
to_roman(40)   == "XL"
to_roman(58)   == "LVIII"
to_roman(1994) == "MCMXCIV"
to_roman(3999) == "MMMCMXCIX"

from_roman("I")        == 1
from_roman("IV")       == 4
from_roman("LVIII")    == 58
from_roman("MCMXCIV")  == 1994
from_roman("MMMCMXCIX") == 3999
```

## Constraints

- `to_roman` only needs to handle `1 <= n <= 3999`.
- `from_roman` only needs to handle valid standard-form numerals in that range.
- `to_roman(from_roman(s)) == s` for every valid `s` in range.
