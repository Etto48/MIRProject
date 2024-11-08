import json
import os
from mir import PROJECT_DIR, DATA_DIR

EXCLUDE_MODULES = [
    "mir.utils.ipynb_compiler",
    "mir.test",
]

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

def remove_main(text: list[str]) -> list[str]:
    """
    Remove the main block from the text.

    # Parameters
    - text (list[str]): The text to remove the main block from.

    # Returns
    - list[str]: The text with the main block removed.
    """
    clean_lines = []
    in_main = False
    for line in text:
        if line.startswith("if __name__ == '__main__':") or line.startswith("if __name__ == \"__main__\":"):
            in_main = True
        elif in_main and not line.startswith(" "*4) and not line.strip() == "":
            in_main = False
        if not in_main:
            clean_lines.append(line)
        
    return clean_lines

def remove_empty_lines_from_end(text: list[str]) -> list[str]:
    """
    Remove empty lines from the end of the text.

    # Parameters
    - text (list[str]): The text to remove empty lines from the end of.

    # Returns
    - list[str]: The text with empty lines removed from the end.
    """
    while text and text[-1].strip() == "":
        text.pop()
    if text:
        text[-1] = text[-1].strip("\n")
    return text

def code_to_cell(text: str | list[str]) -> dict:
    """
    Convert a text to a jupyter notebook cell.

    # Parameters
    - text (str): The text to convert to a cell.

    # Returns
    - dict: The cell in jupyter notebook format.
    """
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {
            "collapsed": False,
            "autoscroll": False
        },
        "outputs": [],
        "source": text.split("\n") if isinstance(text, str) else text
    }

def project_deps_to_notebook_code() -> list[str]:
    """
    Convert the dependencies of a project to a list of notebook shell commands.
    e.g. `!pip3 install pandas

    # Returns
    - list[str]: The list of code cells.
    """
    
    with open(f"{PROJECT_DIR}/pyproject.toml", "r") as f:
        lines = f.readlines()
    deps = []
    in_deps = False
    for line in lines:
        if line.startswith("dependencies = ["):
            in_deps = True
        elif in_deps and "]" in line:
            in_deps = False
        elif in_deps and line.strip() != "":
            deps.append(line.strip().replace("\"","").replace(",","").replace("\'",""))

    return ["# install dependencies"] + [f"!pip3 install {dep}" for dep in deps]


def src_to_ipynb(src_dir: str, doc_dir: str) -> tuple[str, dict]:
    """
    Convert a source directory containing a python project to a Jupyter notebook.

    # Parameters
    - src_dir (str): The source directory containing the python project.
    - doc_dir (str): The directory containing MD documentation to embed in the notebook.

    # Returns
    - str: A single python script containing the entire project.
    - dict: A dict with the jupyter notebook format.
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

    indices_to_remove = []
    for i, module in enumerate(src_modules):
        for e in EXCLUDE_MODULES:
            if module.startswith(e):
                indices_to_remove.append(i)
                break
    indices_to_remove.reverse()
    for i in indices_to_remove:
        src_modules.pop(i)
        src_files.pop(i)

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
        clean_lines = remove_main(clean_lines)
        clean_lines = remove_empty_lines_from_end(clean_lines)
        text = "".join(clean_lines)
        text = f"#%% === {src_files_to_modules[file]} ===\n\n" + text
        sorted_text_for_files.append(text)

    python_script = "\n\n".join(sorted_text_for_files)
    dep_cell = code_to_cell(project_deps_to_notebook_code())
    file_cell = code_to_cell([
        "# define __file__", 
        "import os",
        f"__file__ = os.path.abspath('')",
    ])
    cells = [code_to_cell(text) for text in sorted_text_for_files]
    new_cells = []
    for cell in cells:
        # if all the source code is blank, don't include the cell
        if all(line.strip() == "" for line in cell["source"][1:]):
            continue
        else:
            new_cells.append(cell)
    cells = new_cells

    jupyter_notebook = {
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {
                    "name": "ipython",
                    "version": 3
                },
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "version": "3.12"
            }
        },
        "cells": [dep_cell, file_cell] + cells,
        "nbformat": 4,
        "nbformat_minor": 2,
    }

    return python_script, jupyter_notebook

if __name__ == "__main__":
    src_dir = f"{PROJECT_DIR}/mir"
    doc_dir = f"{PROJECT_DIR}/docs"
    script, notebook = src_to_ipynb(src_dir, doc_dir)
    with open(f"{DATA_DIR}/colab.py", "w") as f:
        f.write(script)
    with open(f"{DATA_DIR}/colab.ipynb", "w") as f:
        json.dump(notebook, f, indent=4)