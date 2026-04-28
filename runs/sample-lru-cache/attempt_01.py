class ListNode: 
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None
nclass LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {} 
        self.head = None
        self.tail = None

    def get(self, key) -> int:
        if key not in self.cache:
            return -1
        node = self.cache[key]
        self.move_to_head(node)
        return node.value

    def put(self, key, value) -> None:
        if key in self.cache:
            node = self.cache[key]
            node.value = value
            self.move_to_head(node)
        else:
            if len(self.cache) >= self.capacity:
                self.evict_least_recently_used()
            node = ListNode(key, value)
            self.cache[key] = node
            self.add_to_head(node)

    def move_to_head(self, node) -> None:
        if self.head == node:
            return
        self.remove_from_list(node)
        if self.head:
            node.next = self.head
            self.head.prev = node
            self.head = node
        else:
            self.tail = node
            self.head = node

    def add_to_head(self, node) -> None:
        if not self.head:
            self.head = node
            self.tail = node
        else:
            node.next = self.head
            self.head.prev = node
            self.head = node

    def remove_from_list(self, node) -> None:
        if node.prev:
            node.prev.next = node.next
        else:
            self.head = node.next
        if node.next:
            node.next.prev = node.prev
        else:
            self.tail = node.prev

    def evict_least_recently_used(self) -> None:
        least_recent = self.tail
        del self.cache[least_recent.key]
        if self.tail == self.head:
            self.head = None
            self.tail = None
        else:
            self.remove_from_list(self.tail)
        self.move_to_head(least_recent)