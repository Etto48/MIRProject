from mir.fs_collections.hashable_key.hashable_key import HashableKey


class StrHK(HashableKey):
    def __init__(self, key: str):
        self.key = key

    def __bytes__(self):
        return self.key.encode()