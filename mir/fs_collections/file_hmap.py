from typing import Optional
from mir.fs_collections.file_list import FileList
import hashlib


class FileHMap:
    """
    This class is a hash map that stores values in a file.
    It uses FileList to store the values.
    Replacing a value is slow because the whole row must be kept in memory and rewritten.
    """
    
    def __init__(self, index: str, path: str, block_size: int = 1024, hash_size: int = 1024*128):
        """
        Initialize the FileHMap.
        
        # Parameters
        - index (str): The path to the index file.
        - path (str): The path to the data file.
        - block_size (int): The size of the blocks in the data file.
        - hash_size (int): The size of the hash table.
        """
        self.inner = FileList(index, path, block_size)
        self.hash_size = hash_size

    def _hash_key(self, key: str) -> int:
        """
        Get the hash key for a key.
        
        # Parameters
        - key (str): The key.
        
        # Returns
        - int: The hash key.
        """
        hash_value = hashlib.sha3_256(key.encode("utf-8"), usedforsecurity=False).digest()
        return int.from_bytes(hash_value, "big") % self.hash_size
        
    def __getitem__(self, key: str) -> Optional[bytes]:
        """
        Get a value from the FileHMap.
        
        # Parameters
        - key (str): The key.
        
        # Returns
        - bytes: The value.
        """
        
        hash_key = self._hash_key(key)
        key_buffer = b""
        value_buffer = b""
        header_buffer = b""
        header = None
        # stage can be 0 for header, 1 for key, 2 for value, 3 for skip until next header
        skipped = 0
        stage = 0
        
        for block in self.inner.get_item_as_stream(hash_key):
            for b in block:
                match stage:
                    case 0:
                        header_buffer += b.to_bytes(1, "big")
                        if len(header_buffer) == 16:
                            header = (
                                int.from_bytes(header_buffer[:8], "big"),
                                int.from_bytes(header_buffer[8:16], "big")
                            )
                            if header[0] == 0:
                                if bytes(key) == b"":
                                    if header[1] == 0:
                                        return b""
                                    else:
                                        stage = 2
                                else:
                                    skipped = 0
                                    stage = 3
                            else:
                                stage = 1
                    case 1:
                        key_buffer += b.to_bytes(1, "big")
                        if len(key_buffer) == header[0]:
                            if bytes(key) == key_buffer:
                                if header[1] == 0:
                                    return b""
                                else:
                                    stage = 2
                            else:
                                skipped = 0
                                stage = 3
                    case 2:
                        value_buffer += b.to_bytes(1, "big")
                        if len(value_buffer) == header[1]:
                            return value_buffer
                    case 3:
                        skipped += 1
                        if skipped == header[1]:
                            key_buffer = b""
                            value_buffer = b""
                            header_buffer = b""
                            header = None
                            stage = 0
        assert stage == 0, "The stream ended unexpectedly."
        return None
    
    def bucket_size_distribution(self) -> list[int]:
        """
        Get the distribution of the bucket sizes.
        
        # Returns
        - list[int]: The number of entries in each bucket.
        """
        ret = []
        for i in range(self.hash_size):
            count = 0
            bucket = self.inner[i]
            header_buffer = b""
            header = None
            skipped = 0
            stage = 0
            for b in bucket:
                match stage:
                    case 0:
                        header_buffer += b.to_bytes(1, "big")
                        if len(header_buffer) == 16:
                            header = (
                                int.from_bytes(header_buffer[:8], "big"),
                                int.from_bytes(header_buffer[8:16], "big")
                            )
                            stage = 1
                            count += 1
                    case 1:
                        skipped += 1
                        if skipped == header[1] + header[0]:
                            header_buffer = b""
                            header = None
                            skipped = 0
                            stage = 0
            ret.append(count)
        return ret      
    
    @staticmethod
    def _kv_as_block(key: str, value: bytes) -> bytes:
        """
        Convert a key-value pair to a block.
        
        # Parameters
        - key (str): The key.
        - value (bytes): The value.
        
        # Returns
        - bytes: The block.
        """
        key_bytes = bytes(key)
        header = len(key_bytes).to_bytes(8, "big") + len(value).to_bytes(8, "big")
        return header + key_bytes + value
    
    def __setitem__(self, key: str, value: Optional[bytes]) -> Optional[bytes]:
        """
        Set a value in the FileHMap.
        
        # Parameters
        - key (str): The key.
        - value (Optional[bytes]): The value to set. If None, the key is removed.
        
        # Returns
        - bytes: The old value.
        """
        
        hash_key = hash(key) % self.hash_size
        
        old_value = self[key]
        if old_value is None:
            # add a new key-value pair
            if value is not None:
                block = self._kv_as_block(key, value)
                self.inner.append(hash_key, block)
            ret = None
        else:
            ret = None
            new_data = b""
            key_buffer = b""
            value_buffer = b""
            header_buffer = b""
            header = None
            # stage can be 0 for header, 1 for key, 2 for change value, 3 for keep value
            stage = 0
            
            for block in self.inner.get_item_as_stream(hash_key):
                for b in block:
                    match stage:
                        case 0:
                            header_buffer += b.to_bytes(1, "big")
                            if len(header_buffer) == 16:
                                header = (
                                    int.from_bytes(header_buffer[:8], "big"),
                                    int.from_bytes(header_buffer[8:16], "big")
                                )
                                if header[0] == 0:
                                    if bytes(key) == b"":
                                        if header[1] == 0:
                                            ret = b""
                                            stage = 3
                                        else:
                                            stage = 2
                                    else:
                                        stage = 3
                                else:
                                    stage = 1
                        case 1:
                            key_buffer += b.to_bytes(1, "big")
                            if len(key_buffer) == header[0]:
                                if bytes(key) == key_buffer:
                                    if header[1] == 0:
                                        ret = b""
                                        stage = 3
                                    else:
                                        stage = 2
                                else:
                                    stage = 3
                        case 2:
                            value_buffer += b.to_bytes(1, "big")
                            if len(value_buffer) == header[1]:
                                ret = value_buffer
                                if value is not None:
                                    new_data += self._kv_as_block(key, value)
                                key_buffer = b""
                                value_buffer = b""
                                header_buffer = b""
                                header = None
                                stage = 0
                        case 3:
                            value_buffer += b.to_bytes(1, "big")
                            if len(value_buffer) == header[1]:
                                new_data += header_buffer + key_buffer + value_buffer
                                key_buffer = b""
                                value_buffer = b""
                                header_buffer = b""
                                header = None
                                stage = 0
            assert stage == 0, "The stream ended unexpectedly."
            self.inner[hash_key] = new_data
        return ret
    
    def __delitem__(self, key: str):
        """
        Delete a key from the FileHMap.
        
        # Parameters
        - key (str): The key.
        """
        self[key] = None

    def __contains__(self, key: str) -> bool:
        """
        Check if a key is in the FileHMap.
        
        # Parameters
        - key (str): The key.
        
        # Returns
        - bool: True if the key is in the FileHMap.
        """
        return self[key] is not None
        
if __name__ == "__main__":
    from mir import DATA_DIR
    import time
    import os
    from itertools import product
    from tqdm.auto import tqdm
    from matplotlib import pyplot as plt
    
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
        data = {}
        
        start = time.time()
        for i in range(1000):
            key = f"key_{i}"
            value = f"value_{i}".encode()
            data[key] = value
            fh[key] = value
        write_time = time.time() - start
        start = time.time()
        for key, value in data.items():
            assert fh[key] == value
        read_time = time.time() - start
        bucket_size_distribution = fh.bucket_size_distribution()
        bs_mean = sum(bucket_size_distribution) / len(bucket_size_distribution)
        bs_std = (sum((x - bs_mean) ** 2 for x in bucket_size_distribution) / len(bucket_size_distribution)) ** 0.5
        
        return {
            "write_time": write_time,
            "read_time": read_time,
            "bs_mean": bs_mean,
            "bs_std": bs_std,
            "index_size": os.path.getsize(index_path),
            "data_size": os.path.getsize(data_path)
        }
        
    write_times = [[0 for _ in hash_space] for _ in block_space]
    read_times = [[0 for _ in hash_space] for _ in block_space]
    bs_means = [[0 for _ in hash_space] for _ in block_space]
    bs_stds = [[0 for _ in hash_space] for _ in block_space]
    index_size = [[0 for _ in hash_space] for _ in block_space]
    data_size = [[0 for _ in hash_space] for _ in block_space]
    total = len(block_space) * len(hash_space)
    
    for (i, block_size), (j, hash_size) in tqdm(product(enumerate(block_space), enumerate(hash_space)), desc="Benchmarking", total=total):
        test_result = test(block_size, hash_size)
        write_times[i][j] = test_result["write_time"]
        read_times[i][j] = test_result["read_time"]
        bs_means[i][j] = test_result["bs_mean"]
        bs_stds[i][j] = test_result["bs_std"]
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
    
    plt.subplot(2, 3, 3)
    plt.title("Bucket Size Mean")
    plt.imshow(bs_means, cmap="viridis")
    plt.colorbar()
    plt.xticks(range(len(hash_space)), hash_space)
    plt.yticks(range(len(block_space)), block_space)
    plt.xlabel("Hash Size")
    plt.ylabel("Block Size")
    
    plt.subplot(2, 3, 4)
    plt.title("Bucket Size Standard Deviation")
    plt.imshow(bs_stds, cmap="viridis")
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