import unittest

from mir.fs_collections.cached_hmap import CachedHMap
from mir.fs_collections.file_hmap import FileHMap
from mir.fs_collections.serde import INT_SERDE
from mir.test.file_list_test_utils import setup_teardown_files


class TestCachedHMap(unittest.TestCase):
    @setup_teardown_files
    def test_file_hmap(self, index_path, data_path):
        fh = FileHMap(index_path, data_path, 16, 4)
        ch = CachedHMap(fh, 4, INT_SERDE)
        data = {
            "pls": 1,
            "hello": 2,
            "this": 3,
            "of": 4,
            "it": 5,
            "caffettin,": 6,
            "lo": 7,
        }
        for k, v in data.items():
            ch[k] = v
        for k, v in data.items():
            self.assertEqual(ch[k], v)
        del ch
        for k, v in data.items():
            self.assertEqual(fh[k], INT_SERDE.serialize(v))

    @setup_teardown_files
    def test_file_hmap_replace(self, index_path, data_path):
        fh = FileHMap(index_path, data_path, 16, 4)
        ch = CachedHMap(fh, 4, INT_SERDE)
        data = {
            "pls": 1,
            "hello": 2,
            "this": 3,
            "of": 4,
            "it": 5,
            "caffettin,": 6,
            "lo": 7,
        }
        for k, v in data.items():
            ch[k] = v
        new_data = {
            "pls": 8,
            "hello": 9,
            "this": 10,
            "of": 11,
            "it": 12,
            "caffettin,": 13,
            "lo": 14,
        }
        for k, v in new_data.items():
            ch[k] = v
        for k, v in new_data.items():
            self.assertEqual(ch[k], v)
        del ch
        for k, v in new_data.items():
            self.assertEqual(fh[k], INT_SERDE.serialize(v))

    @setup_teardown_files
    def test_file_hmap_remove(self, index_path, data_path):
        fh = FileHMap(index_path, data_path, 16, 4)
        ch = CachedHMap(fh, 4, INT_SERDE)
        data = {
            "pls": 1,
            "hello": 2,
            "this": 3,
            "of": 4,
            "it": 5,
            "caffettin,": 6,
            "lo": 7,
        }
        for k, v in data.items():
            ch[k] = v
        for k, v in data.items():
            self.assertEqual(ch[k], v)
        for i, k in enumerate(data.keys()):
            if i % 2 == 0:
                del ch[k]
        for i, k in enumerate(data.keys()):
            if i % 2 == 0:
                self.assertEqual(ch[k], None)
            else:
                self.assertEqual(ch[k], data[k])
        del ch
        for i, k in enumerate(data.keys()):
            if i % 2 == 0:
                self.assertEqual(fh[k], None)
            else:
                self.assertEqual(fh[k], INT_SERDE.serialize(data[k]))


if __name__ == '__main__':
    unittest.main()
