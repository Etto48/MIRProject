import os


class FileMap:
    """
    This class is a simple key-value store that stores values in a file.
    Keys are integers and values are bytes.
    The index file stores the offset and length of the value in the data file.
    The data file stores the values in blocks of a fixed size.
    Blocks are linked together by storing the offset of the next block at the end of the block.
    Shrinking the value will work, but the blocks will not be deallocated.
    The size of the index file depends on the maximum key used.
    """
    
    def __init__(self, index: str, path: str, block_size: int = 1024):
        """
        Initialize the FileMap.
        
        # Parameters
        - index (str): The path to the index file.
        - path (str): The path to the data file.
        - block_size (int): The size of the blocks in the data file.
        """
        
        os.makedirs(os.path.dirname(index), exist_ok=True)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.index_path = index
        if not os.path.exists(index):
            with open(index, "wb") as f:
                pass
        self.path = path
        if not os.path.exists(path):
            with open(path, "wb") as f:
                pass
        self.next_offset_size = 8
        if block_size < self.next_offset_size + 1:
            raise ValueError("Block size too small, must be at least 9 bytes")
        self.block_size = block_size

    def _index_get(self, key: int) -> tuple[int, int]:
        if os.path.getsize(self.index_path) < (key + 1) * 16:
            raise KeyError
        with open(self.index_path, "rb") as f:
            f.seek(key * 16)
            offset = int.from_bytes(f.read(8), "big")
            length = int.from_bytes(f.read(8), "big")
            if offset == 0 and length == 0:
                raise KeyError
            return offset, length

    def _index_set(self, key: int, value: tuple[int, int]) -> None:
        with open(self.index_path, "r+b") as f:
            f.seek(key * 16)
            f.write(value[0].to_bytes(8, "big"))
            f.write(value[1].to_bytes(8, "big"))

    def __getitem__(self, key: int) -> bytes:
        """
        Get a value from the FileMap.
        
        # Parameters
        - key (int): The key of the value.
        # Returns
        - bytes: The value. Setting a value to b"" will delete it.
        """
        
        offset, length = self._index_get(key)
        ret = b""
        size_read = 0
        with open(self.path, "rb") as f:
            while True:
                f.seek(offset)
                block = f.read(self.block_size)
                if len(block) < self.block_size:
                    raise ValueError("Corrupted file")
                size_read += self.block_size - self.next_offset_size
                ret += block[:self.block_size - self.next_offset_size]
                next_offset = int.from_bytes(
                    block[self.block_size - self.next_offset_size:], "big")
                if next_offset == 0:
                    break
                offset = next_offset
        return ret[:length]

    def __setitem__(self, key: int, value: bytes) -> None:
        """
        Set a value in the FileMap.
        
        # Parameters
        - key (int): The key of the value.
        - value (bytes): The value.
        """
        
        file_size = os.path.getsize(self.path)
        value_length = len(value)
        try:
            offset, length = self._index_get(key)
            overwriting = True
            if len(value) < length:
                # cannot deallocate blocks, so we need to overwrite the value in place
                value += b'\x00' * (length - len(value))
        except KeyError:
            offset = file_size
            overwriting = False

        starting_offset = offset
        i = 0

        with open(self.path, "r+b") as f:
            while True:
                f.seek(offset)
                if overwriting:
                    old_block = f.read(self.block_size)
                    next_offset = int.from_bytes(
                        old_block[self.block_size - self.next_offset_size:], "big")
                else:
                    next_offset = 0
                start_offset = i*(self.block_size - self.next_offset_size)
                end_offset = (i+1)*(self.block_size - self.next_offset_size)
                end_offset = min(end_offset, len(value))
                new_block = value[start_offset:end_offset]
                new_block += b'\x00' * \
                    (self.block_size - len(new_block) - self.next_offset_size)
                is_last_block = len(value) == end_offset
                if is_last_block:
                    new_block += b'\x00' * self.next_offset_size
                else:
                    if next_offset == 0:
                        overwriting = False
                        next_offset = file_size
                        file_size += self.block_size
                        next_offset += self.block_size
                        new_block += next_offset.to_bytes(
                            self.next_offset_size, "big")
                    else:
                        new_block += next_offset.to_bytes(
                            self.next_offset_size, "big")
                f.seek(offset)
                f.write(new_block)
                if is_last_block:
                    break
                offset = next_offset
                i += 1

        self._index_set(key, (starting_offset, value_length))

    def next_key(self) -> int:
        """
        Return the next available key. Deleted keys are not reused.
        To get the next key, including deleted keys, use next_available_key.
        The time complexity of this method is O(1).
        """
        return os.path.getsize(self.index_path) // 16
    
    def next_available_key(self) -> int:
        """
        Return the next available key, including deleted keys.
        This method is significantly slower than next_key.
        The time complexity of this method is O(next_key(self)).
        """
        
        for i in range(self.next_key()):
            try:
                self._index_get(i)
            except KeyError:
                return i
        return self.next_key()