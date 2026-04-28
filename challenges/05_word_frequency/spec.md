# Word Frequency

Implement `word_freq(text: str) -> dict[str, int]` in `solution.py`.

Return a dict mapping each *word* in `text` to the number of times it occurs.
Word counting must be:

- **case-insensitive** — `"The"` and `"the"` count as the same word, and the
  key in the returned dict is the lowercase form.
- **punctuation-stripped** — strip ASCII punctuation (`.,!?;:'"()[]{}`) from
  the *edges* of every token. Internal apostrophes, hyphens, and digits
  inside a token stay (so `"don't"` and `"co-op"` are each one word).
- whitespace-separated — split on any run of whitespace.

The empty string maps to an empty dict.

## Examples

```python
word_freq("")                              == {}
word_freq("hello")                         == {"hello": 1}
word_freq("Hello hello HELLO")             == {"hello": 3}
word_freq("The quick brown fox.")          == {"the": 1, "quick": 1, "brown": 1, "fox": 1}
word_freq("Don't stop. Don't!")            == {"don't": 2, "stop": 1}
word_freq("a b a c b a")                   == {"a": 3, "b": 2, "c": 1}
```

## Constraints

- Pure function. No I/O.
- Order of keys in the returned dict does not matter.
- Tokens that become the empty string after stripping (e.g. a lone `","`)
  must NOT appear in the output.
