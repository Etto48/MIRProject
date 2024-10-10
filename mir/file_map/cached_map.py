from collections import OrderedDict
from mir.file_map.cache_entry import CacheEntry
from mir.file_map.file_map import FileMap
        
class CachedMap:
    """
    Cached wrapper around a FileMap.
    """
    def __init__(self, file_map: FileMap, cache_size: int):
        """
        Initialize a CachedMap.
        
        # Parameters
        - file_map (FileMap): The FileMap to wrap.
        - cache_size (int): The maximum number of entries to cache.
        """
        self.inner = file_map
        self.cache: OrderedDict[int, CacheEntry] = OrderedDict()
        self.cache_size = cache_size
        self.next_key_value = self.inner.next_key()
        
    def __getitem__(self, key: int) -> bytes:
        """
        Retrieve a value from the cache or the inner FileMap.
        
        # Parameters
        - key (int): The key to retrieve.
        
        # Returns
        - bytes: The value associated with the key.
        """
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key].value
        value = self.inner[key]
        self.cache[key] = CacheEntry(value)
        if len(self.cache) > self.cache_size:
            old_key, old_value = self.cache.popitem(last=False)
            if old_value.dirty:
                self.inner[old_key] = old_value.value
        return value
    
    def __setitem__(self, key: int, value: bytes):
        """
        Set a value in the cache or the inner FileMap.
        
        # Parameters
        - key (int): The key to set.
        - value (bytes): The value to set.
        """
        if key in self.cache:
            self.cache.move_to_end(key)
            self.cache[key].update(value)
        else:
            self.next_key_value = max(self.next_key_value, key + 1)
            entry = CacheEntry(value)
            entry.dirty = True
            self.cache[key] = entry
            if len(self.cache) > self.cache_size:
                old_key, old_value = self.cache.popitem(last=False)
                if old_value.dirty:
                    self.inner[old_key] = old_value.value
    
    def append(self, key: int, value: bytes):
        """
        Append a value to the value in the cache or the inner FileMap.
        
        # Parameters
        - key (int): The key to append to.
        - value (bytes): The value to append.
        """
        if key in self.cache:
            self.cache.move_to_end(key)
            self.cache[key].append(value)
        else:
            self.next_key_value = max(self.next_key_value, key + 1)
            old = self.inner[key]
            entry = CacheEntry(old + value)
            entry.dirty = True
            self.cache[key] = entry
            if len(self.cache) > self.cache_size:
                old_key, old_value = self.cache.popitem(last=False)
                if old_value.dirty:
                    self.inner[old_key] = old_value.value
    
    def next_key(self) -> int:
        """
        Get the next available key, skipped keys are not considered.
        
        # Returns
        - int: The next available key.
        """
        return self.next_key_value
    
    def write(self):
        """
        Write any dirty values in the cache to the inner FileMap.
        """
        for key, value in self.cache.items():
            if value.dirty:
                self.inner[key] = value.value
            
    def __del__(self):
        """
        Update the inner FileMap with any dirty values in the cache.
        """
        self.write()
    