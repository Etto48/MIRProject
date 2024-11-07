import unittest

from mir.file_map.cached_list import CachedList
from mir.file_map.file_list import FileList
from mir.file_map.serde import INT_SERDE
from mir.test.file_list_test_utils import setup_teardown_files


class TestCachedList(unittest.TestCase):
    @setup_teardown_files
    def test_file_map_add(self, index_path, data_path):
        fm = FileList(index_path, data_path, 16)
        cm = CachedList(fm, 4, INT_SERDE)
        data = [x for x in range(10)]
        for i, d in enumerate(data):
            cm[i] = d
        for i, d in enumerate(data):
            self.assertEqual(cm[i], d)
        del cm
        for i, d in enumerate(data):
            self.assertEqual(fm[i], INT_SERDE.serialize(d))

    @setup_teardown_files
    def test_file_map_next_key(self, index_path, data_path):
        fm = FileList(index_path, data_path, 16)
        cm = CachedList(fm, 4, INT_SERDE)
        data = [x for x in range(10)]
        for i, d in enumerate(data):
            cm[i] = d
        self.assertEqual(cm.next_key(), len(data))
        cm[len(data) + 5] = 0
        self.assertEqual(cm.next_key(), len(data) + 6)
        del cm
        self.assertEqual(fm.next_key(), len(data) + 6)


if __name__ == "__main__":
    unittest.main()
