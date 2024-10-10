import os
from typing import Callable

from mir import DATA_DIR


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