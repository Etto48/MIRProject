from collections import OrderedDict
from typing import Callable, Generic, Optional, TypeVar, get_args
from mir.file_map.cache_entry import CacheEntry
from mir.file_map.file_list import FileList
from mir.file_map.serde import Serde

T = TypeVar('T')


class CachedList(Generic[T]):
    """
    Cached wrapper around a FileList.
    """

    def __init__(self, file_map: FileList, cache_size: int, serde: Serde[T]):
        """
        Initialize a CachedList.

        # Parameters
        - file_map (FileList): The FileList to wrap.
        - cache_size (int): The maximum number of entries to cache.
        - serde (Serde): The Serde class that contains the serialization and deserialization functions.
        """
        self.inner = file_map
        self.cache: OrderedDict[int, CacheEntry[T]] = OrderedDict()
        self.cache_size = cache_size
        self.next_key_value = self.inner.next_key()
        self.serde = serde
        assert isinstance(self.serde, Serde), f"serde must be an instance of Serde, not {
            type(self.serde)}"

    def _cache_pop(self):
        """
        Pop the least recently used value from the cache and write it to the inner FileList.
        """
        old_key, old_value = self.cache.popitem(last=False)
        if old_value.dirty:
            self.inner[old_key] = self.serde.serialize(old_value.value)

    def __getitem__(self, key: int) -> T:
        """
        Retrieve a value from the cache or the inner FileList.

        # Parameters
        - key (int): The key to retrieve.

        # Returns
        - T: The value associated with the key.
        """
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key].value
        else:
            value = self.inner[key]
            value = self.serde.deserialize(value)
            self.cache[key] = CacheEntry(value)
            if len(self.cache) > self.cache_size:
                self._cache_pop()
            return value

    def __setitem__(self, key: int, value: T):
        """
        Set a value in the cache or the inner FileList.

        # Parameters
        - key (int): The key to set.
        - value (T): The value to set.
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
                self._cache_pop()

    def next_key(self) -> int:
        """
        Get the next available key, skipped keys are not considered.

        # Returns
        - int: The next available key.
        """
        return self.next_key_value

    def write(self):
        """
        Write any dirty values in the cache to the inner FileList.
        """
        for key, value in self.cache.items():
            if value.dirty:
                self.inner[key] = self.serde.serialize(value.value)

    def __del__(self):
        """
        Update the inner FileList with any dirty values in the cache.
        """
        self.write()
