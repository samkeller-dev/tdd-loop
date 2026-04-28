from solution import LRUCache


def test_basic_put_get():
    c = LRUCache(2)
    c.put(1, 1)
    c.put(2, 2)
    assert c.get(1) == 1
    assert c.get(2) == 2


def test_missing_key_returns_minus_one():
    c = LRUCache(2)
    assert c.get(99) == -1


def test_eviction_of_lru_after_get():
    c = LRUCache(2)
    c.put(1, 1)
    c.put(2, 2)
    assert c.get(1) == 1   # 1 is now MRU
    c.put(3, 3)            # evicts 2
    assert c.get(2) == -1
    assert c.get(1) == 1
    assert c.get(3) == 3


def test_eviction_full_sequence():
    c = LRUCache(2)
    c.put(1, 1)
    c.put(2, 2)
    assert c.get(1) == 1
    c.put(3, 3)        # evicts 2
    assert c.get(2) == -1
    c.put(4, 4)        # evicts 1
    assert c.get(1) == -1
    assert c.get(3) == 3
    assert c.get(4) == 4


def test_put_existing_key_updates_value_and_refreshes():
    c = LRUCache(2)
    c.put(1, 1)
    c.put(2, 2)
    c.put(1, 100)      # 1 is now MRU and value updated
    c.put(3, 3)        # evicts 2, not 1
    assert c.get(1) == 100
    assert c.get(2) == -1
    assert c.get(3) == 3


def test_capacity_one():
    c = LRUCache(1)
    c.put(1, 1)
    c.put(2, 2)
    assert c.get(1) == -1
    assert c.get(2) == 2


def test_get_missing_does_not_insert():
    c = LRUCache(2)
    c.put(1, 1)
    c.get(99)          # should not occupy a slot
    c.put(2, 2)        # both 1 and 2 fit
    assert c.get(1) == 1
    assert c.get(2) == 2


def test_does_not_exceed_capacity():
    c = LRUCache(3)
    for i in range(10):
        c.put(i, i)
    # Last 3 keys should be present, earlier ones evicted.
    present = sum(1 for i in range(10) if c.get(i) != -1)
    assert present == 3
