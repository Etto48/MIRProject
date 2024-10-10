from collections import OrderedDict
from typing import Optional, TypeVar
from mir.file_map.cache_entry import CacheEntry
from mir.file_map.file_hmap import FileHMap
from mir.file_map.hashable_key.hashable_key import HashableKey
from mir.file_map.serde import Serde

T = TypeVar('T', bound=Serde)

class CachedHMap:
    """
    Cached wrapper around a FileHMap.
    """
    def __init__(self, file_hmap: FileHMap, cache_size: int, serde: type[T]):
        """
        Initialize a CachedHMap.
        
        # Parameters
        - file_hmap (FileHMap): The FileHMap to wrap.
        - cache_size (int): The maximum number of entries to cache.
        - serde (type[T]): The Serde type to use for serialization and deserialization.
        """
        self.inner = file_hmap
        self.cache: OrderedDict[HashableKey, CacheEntry[T]] = OrderedDict()
        self.cache_size = cache_size
        self.serde = serde
        
    def _pop_cache(self):
        """
        Pop the least recently used value from the cache and write it to the inner FileHMap.
        """
        old_key, old_value = self.cache.popitem(last=False)
        if old_value.dirty:
            self.inner[old_key] = old_value.value.serialize()
    
    def __getitem__(self, key: HashableKey) -> Optional[T]:
        """
        Retrieve a value from the cache or the inner FileHMap.
        
        # Parameters
        - key (HashableKey): The key to retrieve.
        
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
                    value = self.serde.deserialize(something)
                    self.cache[key] = CacheEntry(value)
                    if len(self.cache) > self.cache_size:
                        self._pop_cache()
                    return value
    
    def __setitem__(self, key: HashableKey, value: Optional[T]):
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
                    self._pop_cache()
        else:
            del self[key]
    
    def write(self):
        """
        Write any dirty values in the cache to the inner FileHMap.
        """
        for key, value in self.cache.items():
            if value.dirty:
                self.inner[key] = value.value.serialize()
    
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
        
if __name__ == "__main__":
    from mir import DATA_DIR
    import time
    import os
    from itertools import product
    from tqdm.auto import tqdm
    from matplotlib import pyplot as plt
    
    from mir.file_map.hashable_key.impls.str_hk import StrHK
    index_path = f"{DATA_DIR}/test/fhmap.index"
    data_path = f"{DATA_DIR}/test/fhmap.data"
    os.makedirs(f"{DATA_DIR}/test", exist_ok=True)
    block_space = [16, 32, 64, 128, 256, 512, 1024, 2048]
    hash_space = [4, 8, 16, 32, 64, 128, 256, 512]
    
    def test(block_size, hash_size):
        try:
            os.remove(index_path)
        except FileNotFoundError:
            pass
        try:
            os.remove(data_path)
        except FileNotFoundError:
            pass
        fh = FileHMap(index_path, data_path, block_size, hash_size)
        fh = CachedHMap(fh, 100)
        data = {}
        
        start = time.time()
        for i in range(1000):
            key = StrHK(f"key_{i}")
            value = f"value_{i}".encode()
            data[key] = value
            fh[key] = value
        write_time = time.time() - start
        start = time.time()
        for key, value in data.items():
            assert fh[key] == value
        read_time = time.time() - start
        
        return {
            "write_time": write_time,
            "read_time": read_time,
            "index_size": os.path.getsize(index_path),
            "data_size": os.path.getsize(data_path)
        }
        
    write_times = [[0 for _ in hash_space] for _ in block_space]
    read_times = [[0 for _ in hash_space] for _ in block_space]
    index_size = [[0 for _ in hash_space] for _ in block_space]
    data_size = [[0 for _ in hash_space] for _ in block_space]
    total = len(block_space) * len(hash_space)
    
    for (i, block_size), (j, hash_size) in tqdm(product(enumerate(block_space), enumerate(hash_space)), desc="Benchmarking", total=total):
        test_result = test(block_size, hash_size)
        write_times[i][j] = test_result["write_time"]
        read_times[i][j] = test_result["read_time"]
        index_size[i][j] = test_result["index_size"]
        data_size[i][j] = test_result["data_size"]
    os.remove(index_path)
    os.remove(data_path)
    
    plt.figure(figsize=(12, 6))
    plt.subplot(2, 3, 1)
    plt.title("Write Time")
    plt.imshow(write_times, cmap="viridis")
    plt.colorbar()
    plt.xticks(range(len(hash_space)), hash_space)
    plt.yticks(range(len(block_space)), block_space)
    plt.xlabel("Hash Size")
    plt.ylabel("Block Size")
    
    plt.subplot(2, 3, 2)
    plt.title("Read Time")
    plt.imshow(read_times, cmap="viridis")
    plt.colorbar()
    plt.xticks(range(len(hash_space)), hash_space)
    plt.yticks(range(len(block_space)), block_space)
    plt.xlabel("Hash Size")
    plt.ylabel("Block Size")
    
    plt.subplot(2, 3, 5)
    plt.title("Index Size")
    plt.imshow(index_size, cmap="viridis")
    plt.colorbar()
    plt.xticks(range(len(hash_space)), hash_space)
    plt.yticks(range(len(block_space)), block_space)
    plt.xlabel("Hash Size")
    plt.ylabel("Block Size")
    
    plt.subplot(2, 3, 6)
    plt.title("Data Size")
    plt.imshow(data_size, cmap="viridis")
    plt.colorbar()
    plt.xticks(range(len(hash_space)), hash_space)
    plt.yticks(range(len(block_space)), block_space)
    plt.xlabel("Hash Size")
    plt.ylabel("Block Size")
    
    plt.tight_layout()
    plt.show()