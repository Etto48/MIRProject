import unittest

from mir.file_map.cached_map import CachedMap
from mir.file_map.file_map import FileMap
from mir.file_map.serde import IntSerde
from mir.test.file_map_test_utils import setup_teardown_files


class TestCachedMap(unittest.TestCase):
    @setup_teardown_files
    def test_file_map_add(self, index_path, data_path):
        fm = FileMap(index_path, data_path, 16)
        cm = CachedMap(fm, 4, IntSerde)
        data = [IntSerde(x) for x in range(10)]
        for i, d in enumerate(data):
            cm[i] = d
        for i, d in enumerate(data):
            self.assertEqual(cm[i], d)
        del cm
        for i, d in enumerate(data):
            self.assertEqual(fm[i], d.serialize())

    @setup_teardown_files
    def test_file_map_next_key(self, index_path, data_path):
        fm = FileMap(index_path, data_path, 16)
        cm = CachedMap(fm, 4, IntSerde)
        data = [IntSerde(x) for x in range(10)]
        for i, d in enumerate(data):
            cm[i] = d
        self.assertEqual(cm.next_key(), len(data))
        cm[len(data) + 5] = IntSerde(0)
        self.assertEqual(cm.next_key(), len(data) + 6)
        del cm
        self.assertEqual(fm.next_key(), len(data) + 6)


if __name__ == "__main__":
    unittest.main()
