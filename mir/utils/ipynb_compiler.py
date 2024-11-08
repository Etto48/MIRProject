import json
import os
from functools import cmp_to_key
from mir import PROJECT_DIR, DATA_DIR

def is_dependency(mod: str, other_text: list[str]) -> bool:
    """
    Check if a module is a dependency of another module.

    # Parameters
    - mod (str): The module to check if it is a dependency.
    - other_text (list[str]): The text of the other module that may import the first module.

    # Returns
    - bool: Whether the module is a dependency.
    """
    options = [
        f"import {mod}",
        f"from {mod}",
    ]
    if "." in mod:
        split_mod = mod.split(".")
        for i in range(1, len(split_mod)):
            options.extend([
                f"from {'.'.join(split_mod[:i])} import {'.'.join(split_mod[i:])}",
            ])

    for line in other_text:
        for option in options:
            if line.startswith(option):
                return True
    return False

def dependency_cmp(path1: str, mod1: str, path2: str, mod2: str) -> int:
    """
    Compare two modules based on their dependencies.
    """
    with open(path1) as f:
        text1 = f.readlines()
    with open(path2) as f:
        text2 = f.readlines()
    if is_dependency(mod1, text2):
        return -1
    elif is_dependency(mod2, text1):
        return 1
    else:
        return 0
    
def remove_root_imports(text: list[str]) -> list[str]:
    """
    Remove imports that reference the package from the text.

    # Parameters
    - text (list[str]): The text to remove the imports from.

    # Returns
    - list[str]: The text with the imports removed.
    """
    clean_lines = []
    for line in text:
        if line.startswith("from mir") or line.startswith("import mir"):
            clean_lines.append("# " + line)
        else:
            clean_lines.append(line)
    return clean_lines

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

    # topologically sort the files based on their dependencies
    sorted_files = []
    while src_files:
        for file in src_files:
            if all(
                not is_dependency(src_files_to_modules[file], open(other_file).readlines())
                for other_file in src_files
                if other_file != file
            ):
                sorted_files.append(file)
                src_files.remove(file)
                break

    sorted_files.reverse()

    for file in sorted_files:
        print(src_files_to_modules[file])

    sorted_text_for_files = []
    for file in sorted_files:
        with open(file) as f:
            lines = f.readlines()
        clean_lines = remove_root_imports(lines)
        text = "".join(clean_lines)
        text = f"#%% === {src_files_to_modules[file]} ===\n\n" + text
        sorted_text_for_files.append(text)
    
    return "\n\n".join(sorted_text_for_files)

if __name__ == "__main__":
    src_dir = f"{PROJECT_DIR}/mir"
    doc_dir = f"{PROJECT_DIR}/docs"
    nb = src_to_ipynb(src_dir, doc_dir)
    with open(f"{DATA_DIR}/colab.py", "w") as f:
        f.write(nb)