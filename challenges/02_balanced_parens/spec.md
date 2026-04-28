# Balanced Brackets

Implement `is_balanced(s: str) -> bool`.

Return `True` iff every opening bracket in `s` is matched by a closing bracket
of the same kind, in the correct order. Three bracket pairs must be supported:

- `(` … `)`
- `[` … `]`
- `{` … `}`

Characters that are *not* one of these six bracket characters must be ignored
entirely (so `"a(b)c"` is balanced).

The empty string is balanced.

## Examples

```python
is_balanced("")          == True
is_balanced("()")        == True
is_balanced("()[]{}")    == True
is_balanced("([{}])")    == True
is_balanced("(]")        == False
is_balanced("([)]")      == False    # interleaved, not nested
is_balanced("(")         == False    # unclosed
is_balanced(")(")        == False    # closes before it opens
is_balanced("a(b[c]{d})e") == True   # non-bracket chars ignored
```

## Constraints

- Pure function. No regex required (but allowed).
- Handle inputs up to a few thousand characters.
