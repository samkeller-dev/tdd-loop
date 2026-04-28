# FizzBuzz

Implement `fizzbuzz(n: int) -> list[str]`.

For every integer `i` from `1` through `n` inclusive, append a string to the
result list:

- `"FizzBuzz"` if `i` is divisible by 15,
- `"Fizz"`     if `i` is divisible by 3,
- `"Buzz"`     if `i` is divisible by 5,
- otherwise the decimal string representation of `i` (e.g. `"7"`).

The returned list has length `n`, in order from `1` to `n`.

## Examples

```python
fizzbuzz(1)  == ["1"]
fizzbuzz(3)  == ["1", "2", "Fizz"]
fizzbuzz(5)  == ["1", "2", "Fizz", "4", "Buzz"]
fizzbuzz(15) == ["1","2","Fizz","4","Buzz","Fizz","7","8","Fizz","Buzz","11","Fizz","13","14","FizzBuzz"]
```

## Constraints

- `n >= 1` is guaranteed by the tests; you do not need to handle `n <= 0`.
- Pure function: no I/O, no globals, no side effects.
