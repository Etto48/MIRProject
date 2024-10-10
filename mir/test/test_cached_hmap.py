import unittest

from mir.file_map.cached_hmap import CachedHMap
from mir.file_map.file_hmap import FileHMap
from mir.file_map.hashable_key.impls.str_hk import StrHK
from mir.file_map.serde import IntSerde
from mir.test.file_map_test_utils import setup_teardown_files


class TestCachedHMap(unittest.TestCase):
    @setup_teardown_files
    def test_file_hmap(self, index_path, data_path):
        fh = FileHMap(index_path, data_path, 16, 4)
        ch = CachedHMap(fh, 4, IntSerde)
        data = {
            StrHK("pls"): IntSerde(1),
            StrHK("hello"): IntSerde(2),
            StrHK("this"): IntSerde(3),
            StrHK("of"): IntSerde(4),
            StrHK("it"): IntSerde(5),
            StrHK("caffettin,"): IntSerde(6),
            StrHK("lo"): IntSerde(7),
        }
        for k, v in data.items():
            ch[k] = v
        for k, v in data.items():
            self.assertEqual(ch[k], v)
        del ch
        for k, v in data.items():
            self.assertEqual(fh[k], v.serialize())
            
    @setup_teardown_files
    def test_file_hmap_replace(self, index_path, data_path):
        fh = FileHMap(index_path, data_path, 16, 4)
        ch = CachedHMap(fh, 4, IntSerde)
        data = {
            StrHK("pls"): IntSerde(1),
            StrHK("hello"): IntSerde(2),
            StrHK("this"): IntSerde(3),
            StrHK("of"): IntSerde(4),
            StrHK("it"): IntSerde(5),
            StrHK("caffettin,"): IntSerde(6),
            StrHK("lo"): IntSerde(7),
        }
        for k, v in data.items():
            ch[k] = v
        new_data = {
            StrHK("pls"): IntSerde(8),
            StrHK("hello"): IntSerde(9),
            StrHK("this"): IntSerde(10),
            StrHK("of"): IntSerde(11),
            StrHK("it"): IntSerde(12),
            StrHK("caffettin,"): IntSerde(13),
            StrHK("lo"): IntSerde(14),
        }
        for k, v in new_data.items():
            ch[k] = v
        for k, v in new_data.items():
            self.assertEqual(ch[k], v)
        del ch
        for k, v in new_data.items():
            self.assertEqual(fh[k], v.serialize())
            
    @setup_teardown_files
    def test_file_hmap_remove(self, index_path, data_path):
        fh = FileHMap(index_path, data_path, 16, 4)
        ch = CachedHMap(fh, 4, IntSerde)
        data = {
            StrHK("pls"): IntSerde(1),
            StrHK("hello"): IntSerde(2),
            StrHK("this"): IntSerde(3),
            StrHK("of"): IntSerde(4),
            StrHK("it"): IntSerde(5),
            StrHK("caffettin,"): IntSerde(6),
            StrHK("lo"): IntSerde(7),
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
                self.assertEqual(fh[k], data[k].serialize())

if __name__ == '__main__':
    unittest.main()