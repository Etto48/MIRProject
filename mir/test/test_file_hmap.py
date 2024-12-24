import unittest

from mir.fs_collections.file_hmap import FileHMap
from mir.test.file_list_test_utils import setup_teardown_files


class TestFileHMap(unittest.TestCase):
    @setup_teardown_files
    def test_file_hmap(self, index_path, data_path):
        fh = FileHMap(index_path, data_path, 16, 4)
        data = {
            "pls": b"work",
            "hello": b"world",
            "this": b"is a test",
            "of": b"the file map class",
            "it": b"should work",
            "caffettin,": b"caffettin",
            "lo": b"bevo, e so contento",
        }
        for k, v in data.items():
            fh[k] = v
        for k, v in data.items():
            self.assertEqual(fh[k], v)
            
    @setup_teardown_files
    def test_file_hmap_replace(self, index_path, data_path):
        fh = FileHMap(index_path, data_path, 16, 4)
        data = {
            "pls": b"work",
            "hello": b"world",
            "this": b"is a test",
            "of": b"the file map class",
            "it": b"should work",
            "caffettin,": b"caffettin",
            "lo": b"bevo, e so contento",
        }
        for k, v in data.items():
            fh[k] = v
        new_data = {
            "pls": b"work work",
            "hello": b"world world",
            "this": b"is a test test",
            "of": b"the file map class class",
            "it": b"should work work",
            "caffettin,": b"caffettin caffettin",
            "lo": b"bevo, e so contento contento",
        }
        for k, v in new_data.items():
            self.assertEqual(fh.__setitem__(k,v), data[k])
        for k, v in new_data.items():
            self.assertEqual(fh[k], v)
            
    @setup_teardown_files
    def test_file_hmap_remove(self, index_path, data_path):
        fh = FileHMap(index_path, data_path, 16, 4)
        data = {
            "pls": b"work",
            "hello": b"world",
            "this": b"is a test",
            "of": b"the file map class",
            "it": b"should work",
            "caffettin,": b"caffettin",
            "lo": b"bevo, e so contento",
        }
        for k, v in data.items():
            fh[k] = v
        for k, v in data.items():
            self.assertEqual(fh[k], v)
        for i, k in enumerate(data.keys()):
            if i % 2 == 0:
                del fh[k]
        for i, k in enumerate(data.keys()):
            if i % 2 == 0:
                self.assertEqual(fh[k], None)
            else:
                self.assertEqual(fh[k], data[k])

if __name__ == '__main__':
    unittest.main()