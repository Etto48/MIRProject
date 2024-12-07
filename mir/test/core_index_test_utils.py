import os
from typing import Callable

from mir import DATA_DIR


def setup_teardown_folder(func: Callable) -> Callable:
    def wrapper(self):
        index_path = f"{DATA_DIR}/test/"
        try:
            for file in os.listdir(index_path):
                os.remove(f"{index_path}/{file}")
        except FileNotFoundError:
            pass
        func(self, index_path)
        for file in os.listdir(index_path):
            os.remove(f"{index_path}/{file}")
    return wrapper