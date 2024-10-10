from typing import Generic, TypeVar


T = TypeVar('T')


class CacheEntry(Generic[T]):
    """
    This class is used in CachedHMap and CachedMap to store the status of a cached value.
    """

    def __init__(self, value: T):
        self.value = value
        self.dirty = False

    def update(self, value: T):
        self.value = value
        self.dirty = True
