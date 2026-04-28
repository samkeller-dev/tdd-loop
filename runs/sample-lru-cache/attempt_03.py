class LRUCache: 
    def __init__(self, capacity: int):
        self.cache = {} 
        self.order = [] 
        self.capacity = capacity
    
    def get(self, key) -> int:
        if key in self.cache:
            self.order.remove(key)
            self.order.append(key)
            return self.cache[key]
        else:
            return -1
    
    def put(self, key, value) -> None:
        if self.capacity == 0:
            raise ValueError('Cache is full')
        if key in self.cache:
            self.order.remove(key)
            self.order.append(key)
            self.cache[key] = value
        else:
            self.cache[key] = value
            self.order.append(key)
            if len(self.cache) > self.capacity:
                least_recently_used = self.order.pop(0)
                del self.cache[least_recently_used]