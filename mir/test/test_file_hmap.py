import unittest

from mir.file_map.file_hmap import FileHMap
from mir.file_map.hashable_key.impls.str_hk import StrHK
from mir.test.file_list_test_utils import setup_teardown_files


class TestFileHMap(unittest.TestCase):
    @setup_teardown_files
    def test_file_hmap(self, index_path, data_path):
        fh = FileHMap(index_path, data_path, 16, 4)
        data = {
            StrHK("pls"): b"work",
            StrHK("hello"): b"world",
            StrHK("this"): b"is a test",
            StrHK("of"): b"the file map class",
            StrHK("it"): b"should work",
            StrHK("caffettin,"): b"caffettin",
            StrHK("lo"): b"bevo, e so contento",
        }
        for k, v in data.items():
            fh[k] = v
        for k, v in data.items():
            self.assertEqual(fh[k], v)
            
    @setup_teardown_files
    def test_file_hmap_replace(self, index_path, data_path):
        fh = FileHMap(index_path, data_path, 16, 4)
        data = {
            StrHK("pls"): b"work",
            StrHK("hello"): b"world",
            StrHK("this"): b"is a test",
            StrHK("of"): b"the file map class",
            StrHK("it"): b"should work",
            StrHK("caffettin,"): b"caffettin",
            StrHK("lo"): b"bevo, e so contento",
        }
        for k, v in data.items():
            fh[k] = v
        new_data = {
            StrHK("pls"): b"work work",
            StrHK("hello"): b"world world",
            StrHK("this"): b"is a test test",
            StrHK("of"): b"the file map class class",
            StrHK("it"): b"should work work",
            StrHK("caffettin,"): b"caffettin caffettin",
            StrHK("lo"): b"bevo, e so contento contento",
        }
        for k, v in new_data.items():
            self.assertEqual(fh.__setitem__(k,v), data[k])
        for k, v in new_data.items():
            self.assertEqual(fh[k], v)
            
    @setup_teardown_files
    def test_file_hmap_remove(self, index_path, data_path):
        fh = FileHMap(index_path, data_path, 16, 4)
        data = {
            StrHK("pls"): b"work",
            StrHK("hello"): b"world",
            StrHK("this"): b"is a test",
            StrHK("of"): b"the file map class",
            StrHK("it"): b"should work",
            StrHK("caffettin,"): b"caffettin",
            StrHK("lo"): b"bevo, e so contento",
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