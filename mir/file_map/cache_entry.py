class CacheEntry:
    """
    This class is used in CachedHMap and CachedMap to store the status of a cached value.
    """
    def __init__(self, value: bytes):
        self.value = value
        self.dirty = False
    
    def update(self, value: bytes):
        self.value = value
        self.dirty = True
    
    def append(self, value: bytes):
        self.value += value
        self.dirty = True
