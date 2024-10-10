from typing import Callable
import unittest
import os

from mir import DATA_DIR
from mir.file_map.cached_map import CachedMap
from mir.file_map.file_map import FileMap
from mir.test.file_map_test_utils import setup_teardown_files

class TestCachedMap(unittest.TestCase):
    @setup_teardown_files
    def test_file_map_add(self, index_path, data_path):
        fm = FileMap(index_path, data_path, 16)
        cm = CachedMap(fm, 4)
        data = [
            b"pls",
            b"work",
            b"hello world",
            b"this is a test",
            b"of the file map class",
            b"it should work",
            b"caffettin, caffettin",
            b"lo bevo, e so contento",
        ]
        for i, d in enumerate(data):
            cm[i] = d
        for i, d in enumerate(data):
            self.assertEqual(cm[i], d)
        del cm
        for i, d in enumerate(data):
            self.assertEqual(fm[i], d)
        
    @setup_teardown_files
    def test_file_map_next_key(self, index_path, data_path):
        fm = FileMap(index_path, data_path, 16)
        cm = CachedMap(fm, 4)
        data = [
            b"pls",
            b"work",
            b"hello world",
            b"this is a test",
            b"of the file map class",
            b"it should work",
            b"caffettin, caffettin",
            b"lo bevo, e so contento",
        ]
        for i, d in enumerate(data):
            cm[i] = d
        self.assertEqual(cm.next_key(), len(data))
        cm[len(data) + 5] = b"test"
        self.assertEqual(cm.next_key(), len(data) + 6)
        del cm
        self.assertEqual(fm.next_key(), len(data) + 6)
        
    @setup_teardown_files
    def test_file_map_append(self, index_path, data_path):
        fm = FileMap(index_path, data_path, 16)
        cm = CachedMap(fm, 4)
        data = [
            b"pls",
            b"work",
            b"hello world",
            b"this is a test",
            b"of the file map class",
            b"it should work",
            b"caffettin, caffettin",
            b"lo bevo, e so contento",
        ]
        for i, d in enumerate(data):
            cm[i] = d
        for i, d in enumerate(data):
            cm.append(i, d)
        for i, d in enumerate(data):
            cm.append(i, b"TEST")
        for i, d in enumerate(data):
            total = b"".join([d]*2) + b"TEST"
            self.assertEqual(cm[i], total)
        del cm
        for i, d in enumerate(data):
            total = b"".join([d]*2) + b"TEST"
            self.assertEqual(fm[i], total)
            
if __name__ == "__main__":
    unittest.main()