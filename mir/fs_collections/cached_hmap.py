from collections import OrderedDict
from typing import Generic, Optional, TypeVar
from mir.fs_collections.cache_entry import CacheEntry
from mir.fs_collections.file_hmap import FileHMap
from mir.fs_collections.serde import Serde

T = TypeVar('T')


class CachedHMap(Generic[T]):
    """
    Cached wrapper around a FileHMap.
    """

    def __init__(self, file_hmap: FileHMap, cache_size: int, serde: Serde[T]):
        """
        Initialize a CachedHMap.

        # Parameters
        - file_hmap (FileHMap): The FileHMap to wrap.
        - cache_size (int): The maximum number of entries to cache.
        - serde (Serde): The Serde class that contains the serialization and deserialization functions.
        """
        self.inner = file_hmap
        self.cache: OrderedDict[str, CacheEntry[T]] = OrderedDict()
        self.cache_size = cache_size
        self.serde = serde
        assert isinstance(self.serde, Serde), f"serde must be an instance of Serde, not {
            type(self.serde)}"

    def _pop_cache(self):
        """
        Pop the least recently used value from the cache and write it to the inner FileHMap.
        """
        old_key, old_value = self.cache.popitem(last=False)
        if old_value.dirty:
            self.inner[old_key] = self.serde.serialize(old_value.value)

    def __getitem__(self, key: str) -> Optional[T]:
        """
        Retrieve a value from the cache or the inner FileHMap.

        # Parameters
        - key (str): The key to retrieve.

        # Returns
        - Optional[T]: The value associated with the key, or None if the key is not present
        """
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key].value
        else:
            match self.inner[key]:
                case None:
                    return None
                case something:
                    value = self.serde.deserialize(something, key)
                    self.cache[key] = CacheEntry(value)
                    if len(self.cache) > self.cache_size:
                        self._pop_cache()
                    return value

    def __setitem__(self, key: str, value: Optional[T]):
        """
        Set a value in the cache or the inner FileHMap.

        # Parameters
        - key (str): The key to set.
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
                    self._pop_cache()
        else:
            del self[key]

    def write(self):
        """
        Write any dirty values in the cache to the inner FileHMap.
        """
        for key, value in self.cache.items():
            if value.dirty:
                self.inner[key] = self.serde.serialize(value.value)

    def __del__(self):
        """
        Update the inner FileHMap with any dirty values in the cache.
        """
        self.write()

    def __delitem__(self, key: str):
        """
        Delete a key from the cache and the inner FileHMap.

        # Parameters
        - key (str): The key to delete.
        """
        try:
            del self.cache[key]
        except KeyError:
            pass
        del self.inner[key]

    def __contains__(self, key: str) -> bool:
        """
        Check if a key is in the cache or the inner FileHMap.

        # Parameters
        - key (str): The key to check.

        # Returns
        - bool: True if the key is present, False otherwise.
        """
        return key in self.cache or key in self.inner
