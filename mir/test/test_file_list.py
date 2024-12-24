import unittest

from mir import DATA_DIR
from mir.fs_collections.file_list import FileList
from mir.test.file_list_test_utils import setup_teardown_files

class TestFileList(unittest.TestCase):
    @setup_teardown_files
    def test_file_map_add(self, index_path, data_path):
        fm = FileList(index_path, data_path, 16)
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
        fm = FileList(index_path, data_path, 16)
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
        fm = FileList(index_path, data_path, 16)
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
        fm = FileList(index_path, data_path, 16)
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
        fm = FileList(index_path, data_path, 16)
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
        
    @setup_teardown_files
    def test_file_map_stream(self, index_path, data_path):
        fm = FileList(index_path, data_path, 16)
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
            self.assertEqual(b"".join(fm.get_item_as_stream(i)), d)
    
    @setup_teardown_files
    def test_file_map_append(self, index_path, data_path):
        fm = FileList(index_path, data_path, 16)
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
            fm.append(i, d)
        for i, d in enumerate(data):
            fm.append(i, b"TEST")
        for i, d in enumerate(data):
            total = b"".join([d]*2) + b"TEST"
            self.assertEqual(fm[i], total)
            
    @setup_teardown_files
    def test_file_map_concurrent(self, index_path, data_path):
        fm = FileList(index_path, data_path, 16)
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
        
        streams = [
            fm.get_item_as_stream(i) for i in range(len(data))
        ]
        
        output = [b"" for _ in range(len(data))]
        completed = [False for _ in range(len(data))]
        while not all(completed):
            for i, s in enumerate(streams):
                try:
                    output[i] += next(s)
                except StopIteration:
                    completed[i] = True
                # the write is buffered to be written once the
                # stream is closed
                fm[i] = b"TEST"
        for i, d in enumerate(data):
            self.assertEqual(output[i], d)
        for i, d in enumerate(data):
            self.assertEqual(fm[i], b"TEST")
    
    @setup_teardown_files
    def test_file_map_persistency(self, index_path, data_path):
        fm = FileList(index_path, data_path, 16)
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
        del fm


        fm = FileList(index_path, data_path, 16)
        self.assertEqual(fm.next_key(), len(data))
        for i, d in enumerate(data):
            self.assertEqual(fm[i], d)
        
        
            
if __name__ == "__main__":
    unittest.main()