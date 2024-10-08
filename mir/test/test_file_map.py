from typing import Callable
import unittest
import os

from mir import DATA_DIR
from mir.file_map.file_map import FileMap

def setup_teardown_files(func: Callable) -> Callable:
    def wrapper(self):
        index_path = f"{DATA_DIR}/test/file_map_{func.__name__}.index"
        data_path = f"{DATA_DIR}/test/file_map_{func.__name__}.data"
        try:
            os.remove(index_path)
        except FileNotFoundError:
            pass
        try:
            os.remove(data_path)
        except FileNotFoundError:
            pass
        func(self, index_path, data_path)
        os.remove(index_path)
        os.remove(data_path)
    return wrapper

class TestFileMap(unittest.TestCase):
    @setup_teardown_files
    def test_file_map_add(self, index_path, data_path):
        fm = FileMap(index_path, data_path, 16)
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
            fm[i] = d
        for i, d in enumerate(data):
            self.assertEqual(fm[i], d)

    @setup_teardown_files
    def test_file_map_extend(self, index_path, data_path):
        fm = FileMap(index_path, data_path, 16)
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
            fm[i] = d
        new_data = data = [
            b"pls work plspls",
            b"work pleaseeeee",
            b"hello world, hello world",
            b"this is a test, and it is a test",
            b"of the file map class, yes this specific class",
            b"it should work, or else...",
            b"caffettin, caffettin, lo bevo, e so contento",
            b"lo bevo, e so contento, e poiiiiiii",
        ]
        for i, d in enumerate(new_data):
            fm[i] = d
        for i, d in enumerate(new_data):
            self.assertEqual(fm[i], d)
        
    @setup_teardown_files
    def test_file_map_shrink(self, index_path, data_path):
        fm = FileMap(index_path, data_path, 16)
        data = [
            b"pls work plspls",
            b"work pleaseeeee",
            b"hello world, hello world",
            b"this is a test, and it is a test",
            b"of the file map class, yes this specific class",
            b"it should work, or else...",
            b"caffettin, caffettin, lo bevo, e so contento",
            b"lo bevo, e so contento, e poiiiiiii",
        ]
        for i, d in enumerate(data):
            fm[i] = d
        new_data = data = [
            b"pls",
            b"work",
            b"hello world",
            b"this is a test",
            b"of the file map class",
            b"it should work",
            b"caffettin, caffettin",
            b"lo bevo, e so contento",
        ]
        for i, d in enumerate(new_data):
            fm[i] = d
        for i, d in enumerate(new_data):
            self.assertEqual(fm[i], d)
        
    @setup_teardown_files
    def test_file_map_skip_index(self, index_path, data_path):
        fm = FileMap(index_path, data_path, 16)
        data = {
            0: b"pls",
            1: b"work",
            4: b"of the file map class",
            5: b"it should work",
            2: b"hello world",
            3: b"this is a test",
        }
        for i, d in data.items():
            fm[i] = d
        for i, d in data.items():
            self.assertEqual(fm[i], d)
        
    @setup_teardown_files
    def test_file_map_next_key(self, index_path, data_path):
        fm = FileMap(index_path, data_path, 16)
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
            fm[i] = d
        self.assertEqual(fm.next_key(), len(data))
        fm[len(data) + 5] = b"test"
        self.assertEqual(fm.next_key(), len(data) + 6)
        self.assertEqual(fm.next_available_key(), len(data))
        
            
if __name__ == "__main__":
    unittest.main()