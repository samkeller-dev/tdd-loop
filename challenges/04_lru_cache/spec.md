# LRU Cache

Implement a class `LRUCache` in `solution.py`:

```python
class LRUCache:
    def __init__(self, capacity: int): ...
    def get(self, key) -> int: ...     # returns -1 if key is absent
    def put(self, key, value) -> None: ...
```

The cache holds at most `capacity` items. When `put` is called and the cache
is at capacity with a *new* key, the **least-recently-used** existing key
must be evicted before the new key is inserted.

Both `get` and `put` count as "uses" — calling `get(k)` or `put(k, v)` makes
`k` the most-recently-used key. `put(k, v)` on an existing `k` updates its
value and refreshes its recency.

`get` on a missing key returns `-1` and does **not** insert anything.

## Examples

```python
c = LRUCache(2)
c.put(1, 1)
c.put(2, 2)
c.get(1)        # 1   — order is now [2, 1]; 1 is most recently used
c.put(3, 3)     #     — evicts key 2 (least recently used)
c.get(2)        # -1
c.put(4, 4)     #     — evicts key 1
c.get(1)        # -1
c.get(3)        # 3
c.get(4)        # 4
```

## Constraints

- `capacity >= 1`.
- Keys and values are simple hashable scalars (ints in the tests).
- Both operations should be O(1) amortised, but correctness is what is
  graded — the tests do not measure complexity.
