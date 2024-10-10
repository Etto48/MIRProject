from collections import OrderedDict
from typing import Optional
from mir.file_map.cache_entry import CacheEntry
from mir.file_map.file_hmap import FileHMap
from mir.file_map.hashable_key.hashable_key import HashableKey


class CachedHMap:
    """
    Cached wrapper around a FileHMap.
    """
    def __init__(self, file_hmap: FileHMap, cache_size: int):
        """
        Initialize a CachedHMap.
        
        # Parameters
        - file_hmap (FileHMap): The FileHMap to wrap.
        - cache_size (int): The maximum number of entries to cache.
        """
        self.inner = file_hmap
        self.cache: OrderedDict[HashableKey, CacheEntry] = OrderedDict()
        self.cache_size = cache_size
    
    def __getitem__(self, key: HashableKey) -> Optional[bytes]:
        """
        Retrieve a value from the cache or the inner FileHMap.
        
        # Parameters
        - key (HashableKey): The key to retrieve.
        
        # Returns
        - Optional[bytes]: The value associated with the key, or None if the key is not present
        """
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key].value
        else:
            match self.inner[key]:
                case None:
                    return None
                case something:
                    self.cache[key] = CacheEntry(something)
                    if len(self.cache) > self.cache_size:
                        old_key, old_value = self.cache.popitem(last=False)
                        if old_value.dirty:
                            self.inner[old_key] = old_value.value
                    return something
    
    def __setitem__(self, key: HashableKey, value: Optional[bytes]):
        """
        Set a value in the cache or the inner FileHMap.
        
        # Parameters
        - key (HashableKey): The key to set.
        - value (Optional[bytes]): The value to set, or None to delete the key.
        """
        if value is not None:
            if key in self.cache:
                self.cache.move_to_end(key)
                self.cache[key].update(value)
            else:
                entry = CacheEntry(value)
                entry.dirty = True
                self.cache[key] = entry
                if len(self.cache) > self.cache_size:
                    old_key, old_value = self.cache.popitem(last=False)
                    if old_value.dirty:
                        self.inner[old_key] = old_value.value
        else:
            del self[key]
    
    def write(self):
        """
        Write any dirty values in the cache to the inner FileHMap.
        """
        for key, value in self.cache.items():
            if value.dirty:
                self.inner[key] = value.value
    
    def __del__(self):
        """
        Update the inner FileHMap with any dirty values in the cache.
        """
        self.write()
    
    def __delitem__(self, key: HashableKey):
        """
        Delete a key from the cache and the inner FileHMap.
        
        # Parameters
        - key (HashableKey): The key to delete.
        """
        try:
            del self.cache[key]
        except KeyError:
            pass
        del self.inner[key]