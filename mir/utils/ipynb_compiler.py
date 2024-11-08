import json
import os
from functools import cmp_to_key
from mir import PROJECT_DIR, DATA_DIR

def is_a_dependency(path1: str, mod1: str, path2: str, mod2: str) -> int:
    with open(path1) as f:
        text1 = f.read()
    with open(path2) as f:
        text2 = f.read()
    if mod1 in text2:
        return -1
    if mod2 in text1:
        return 1
    return 0
    

def src_to_ipynb(src_dir: str, doc_dir: str) -> str:
    """
    Convert a source directory containing a python project to a Jupyter notebook.

    # Parameters
    - src_dir (str): The source directory containing the python project.
    - doc_dir (str): The directory containing MD documentation to embed in the notebook.
    """

    # get all files in the src dir recursively, ignoring __pycache__ dirs
    src_files: list[str] = []
    for root, _, files in os.walk(src_dir):
        if "__pycache__" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                src_files.append(os.path.join(root, file))
    
    src_modules = [
        file.replace(src_dir, "mir").replace("/", ".").replace(".py", "")
        for file in src_files
    ]

    src_modules = [
        (module if not module.endswith(".__init__") else module.replace(".__init__","") ) for module in src_modules
    ]

    src_modules_to_files = dict(zip(src_modules, src_files))
    src_files_to_modules = dict(zip(src_files, src_modules))
    
    # get all files in the doc dir
    doc_files = []
    for root, _, files in os.walk(doc_dir):
        for file in files:
            doc_files.append(os.path.join(root, file))

    sorted_files = sorted(src_files, key=cmp_to_key(lambda f1, f2: is_a_dependency(f1, src_files_to_modules[f1], f2, src_files_to_modules[f2])))
    for file in sorted_files:
        print(src_files_to_modules[file])

    raise NotImplementedError


if __name__ == "__main__":
    src_dir = f"{PROJECT_DIR}/mir"
    doc_dir = f"{PROJECT_DIR}/docs"
    nb = src_to_ipynb(src_dir, doc_dir)
    with open(f"{DATA_DIR}/colab.ipynb", "w") as f:
        f.write(nb)