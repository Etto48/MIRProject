from mir.file_map.hashable_key.hashable_key import HashableKey


class StrHK(HashableKey):
    def __init__(self, key: str):
        self.key = key

    def __hash__(self):
        return hash(self.key)

    def __bytes__(self):
        return self.key.encode()