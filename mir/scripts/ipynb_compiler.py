import inspect
import json
import os
import time
from typing import Optional
from mir import PROJECT_DIR, DATA_DIR

EXCLUDE_MODULES = [
    "mir.scripts",
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
                f"from {'.'.join(split_mod[:i])} "
                f"import {'.'.join(split_mod[i:])}",
            ])

    for line in other_text:
        for option in options:
            if line.startswith(option):
                return True
    return False


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


def remove_redundant_imports(text: list[str], used_imports: set[str]) -> list[str]:
    """
    Remove imports that are not used in the text.

    # Parameters
    - text (list[str]): The text to remove the imports from.
    - used_imports (set[str]): The set of imports that are used in the text.

    # Returns
    - list[str]: The text with the unused imports removed.
    """
    clean_lines = []
    for line in text:
        if line.startswith("import "):
            if line.split(" ")[1] in used_imports:
                clean_lines.append("# " + line)
            else:
                clean_lines.append(line)
                used_imports.add(line.split(" ")[1])
        else:
            clean_lines.append(line)
    return clean_lines


def remove_empty_cells(cells: list[dict]) -> list[dict]:
    """
    Remove empty cells from a list of cells.

    # Parameters
    - cells (list[dict]): The list of cells to remove the empty cells from.

    # Returns
    - list[dict]: The list of cells with the empty cells removed.
    """
    new_cells = []
    for cell in cells:
        # if all the source code is blank, don't include the cell
        if all(line.strip() == "" for line in cell["source"][1:]):
            continue
        else:
            new_cells.append(cell)
    return new_cells


def get_module_name_from_cell(cell: dict) -> Optional[str]:
    """
    Get the module name from a cell.

    # Parameters
    - cell (dict): The cell to get the module name from.

    # Returns
    - Optional[str]: The module name if available.
    """

    if cell["source"][0].startswith("#%% === "):
        return cell["source"][0].split("===")[1].strip()
    else:
        return None


def code_to_cell(text: str | list[str]) -> dict:
    """
    Convert a code block to a jupyter notebook cell.

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


def doc_to_cell(text: str | list[str]) -> dict:
    """
    Convert a documentation piece to a jupyter notebook cell.

    # Parameters
    - text (str): The text to convert to a cell.

    # Returns
    - dict: The cell in jupyter notebook format.
    """
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": text.split("\n") if isinstance(text, str) else text
    }


def project_deps_to_notebook_code(src_dir: str) -> list[str]:
    """
    Convert the dependencies of a project to a list of notebook shell commands.
    e.g. `!pip3 install pandas

    # Parameters
    - src_dir (str): The source directory of the project. 
    The parent of this directory must contain a `pyproject.toml` file.

    # Returns
    - list[str]: The list of code cells.
    """

    project_dir = os.path.dirname(src_dir)

    with open(f"{project_dir}/pyproject.toml", "r") as f:
        lines = f.readlines()
    deps = []
    in_deps = False
    for line in lines:
        if line.startswith("dependencies = ["):
            in_deps = True
        elif in_deps and "]" in line:
            in_deps = False
        elif in_deps and line.strip() != "":
            deps.append(line.strip().replace(
                "\"", "").replace(",", "").replace("\'", ""))

    return ["# install dependencies"] + [f"!pip3 install {dep}" for dep in deps]


def c(s: str, color: str, tabs: int = 0) -> str:
    """
    Color a string for printing.

    # Parameters
    - s (str): The string to color.
    - color (str): The color to use.
    - tabs (int): The number of tabs to add before the string.

    # Returns
    - str: The colored string.
    """
    colors = {
        "black": 30,
        "red": 31,
        "green": 32,
        "yellow": 33,
        "blue": 34,
        "magenta": 35,
        "cyan": 36,
        "white": 37,
        "gray": 90,
        "bright_red": 91,
        "bright_green": 92,
        "bright_yellow": 93,
        "bright_blue": 94,
        "bright_magenta": 95,
        "bright_cyan": 96,
        "bright_white": 97,
    }
    return " "*4*tabs + f"\033[{colors[color]}m{s}\033[0m"


def list_modules(src_dir: str) -> tuple[list[str], dict[str, str]]:
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
        (
            module if not module.endswith(".__init__")
            else module.replace(".__init__", "")
        ) for module in src_modules
    ]

    indices_to_remove = []
    for i, module in enumerate(src_modules):
        for e in EXCLUDE_MODULES:
            if module.startswith(e):
                indices_to_remove.append(i)
                print(c(module, "gray", 1))
                break
        else:
            print(c(module, "white", 1))
    indices_to_remove.reverse()
    for i in indices_to_remove:
        src_modules.pop(i)
        src_files.pop(i)

    src_files_to_modules = dict(zip(src_files, src_modules))
    return src_files, src_files_to_modules


def list_docs(doc_dir: str) -> list[str]:
    doc_files = []
    for root, _, files in os.walk(doc_dir):
        for file in files:
            if file.endswith(".md"):
                doc_files.append(os.path.join(root, file))
                print(c(f"docs/{file}", "white", 1))
    return doc_files


def topological_sort(src_files: list[str], src_files_to_modules: dict[str, str]) -> list[str]:
    # topologically sort the files based on their dependencies
    sorted_files = []
    src_files.sort(reverse=True)
    while src_files:
        for file in src_files:
            if all(
                not is_dependency(
                    src_files_to_modules[file], open(other_file).readlines())
                for other_file in src_files
                if other_file != file
            ):
                sorted_files.append(file)
                src_files.remove(file)
                break
        else:
            print(c("Cyclic dependency detected", "bright_red"))
            exit(1)
    sorted_files.reverse()
    return sorted_files


def load_and_clean_files(sorted_files: list[str], src_files_to_modules: dict[str, str]) -> list[str]:
    sorted_text_for_files = []
    used_imports = set()
    for file in sorted_files:
        with open(file) as f:
            lines = f.readlines()
        clean_lines = remove_root_imports(lines)
        clean_lines = remove_main(clean_lines)
        clean_lines = remove_empty_lines_from_end(clean_lines)
        clean_lines = remove_redundant_imports(clean_lines, used_imports)
        text = "".join(clean_lines)
        text = f"#%% === {src_files_to_modules[file]} ===\n\n" + text
        sorted_text_for_files.append(text)
    return sorted_text_for_files


def compile_python_script(sorted_text_for_files: list[str]) -> str:
    return "\n\n".join(sorted_text_for_files)


def compile_code_cells(sorted_text_for_files: list[str]) -> list[dict]:
    dep_cell = code_to_cell(project_deps_to_notebook_code(src_dir))
    file_cell = code_to_cell([
        "# define __file__",
        "import os",
        f"__file__ = os.path.abspath('')",
    ])
    cells = [code_to_cell(text) for text in sorted_text_for_files]
    cells = remove_empty_cells(cells)
    cells = [dep_cell, file_cell] + cells

    return cells


def load_doc(doc_files: list[str]) -> list[tuple[Optional[str], str]]:
    doc_text_for_files: list[tuple[Optional[str], str]] = []
    for file in doc_files:
        module_name = None
        with open(file) as f:
            lines = f.readlines()
        prefix = "<!-- module:"
        postfix = "-->\n"
        if lines and lines[0].startswith(prefix) and lines[0].endswith(postfix):
            module_name = lines[0][len(prefix):len(
                lines[0])-len(postfix)].strip()
            print(
                c(
                    f"\"docs/{os.path.basename(file)}\" -> {module_name}",
                    "bright_magenta",
                    1
                )
            )
            lines = lines[1:]
        doc_text_for_files.append((module_name, "".join(lines)))
    return doc_text_for_files


def order_docs(
        cell_modules: list[Optional[str]],
        doc_text_for_files: list[tuple[Optional[str], str]],
        doc_files: list[str]) -> tuple[list[tuple[Optional[str], str]], list[str]]:
    module_index_hashmap = {module: i for i, module in enumerate(
        cell_modules) if module is not None}
    # sort the documentation files based on the order of the modules
    sorted_doc_text_for_files, sorted_doc_files = zip(
        *sorted(zip(doc_text_for_files, doc_files), key=lambda x: module_index_hashmap.get(x[0][0], 0))
    )
    return sorted_doc_text_for_files, sorted_doc_files


def merge_code_and_doc_cells(
        cells: list[dict],
        sorted_doc_text_for_files: list[tuple[Optional[str], str]],
        sorted_doc_files: list[str],
        cell_modules: list[Optional[str]]) -> list[dict]:
    # add the documentation cells to the right places
    module_path = __file__.replace(PROJECT_DIR, "")[:-3]
    module_name = module_path.replace("/", ".")[1:]
    new_cells = [
        doc_to_cell(
            f"This notebook was automatically generated with our custom script ({module_name})"
        )
    ]
    doc_index = 0
    for module, cell in zip(cell_modules, cells):
        while doc_index < len(sorted_doc_text_for_files) and sorted_doc_text_for_files[doc_index][0] == module:
            if module is not None:
                print(
                    c(
                        f"Adding doc \"docs/{os.path.basename(
                            sorted_doc_files[doc_index])}\""
                        f" before {module}",
                        "bright_magenta",
                        1
                    )
                )
            else:
                print(
                    c(
                        f"Adding doc \"docs/{os.path.basename(
                            sorted_doc_files[doc_index])}\" "
                        "at the beginning",
                        "bright_magenta",
                        1
                    )
                )
            new_cells.append(doc_to_cell(
                sorted_doc_text_for_files[doc_index][1]))
            doc_index += 1
        new_cells.append(cell)
    return new_cells


def compile_notebook(cells: list[dict]) -> dict:
    jupyter_notebook = {
        "metadata": {
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
        "cells": cells,
        "nbformat": 4,
        "nbformat_minor": 2,
    }
    return jupyter_notebook


def src_to_ipynb(src_dir: str, doc_dir: str, output_dir: str) -> tuple[str, str]:
    """
    Convert a source directory containing a python project to a Jupyter notebook.

    # Parameters
    - src_dir (str): The source directory containing the python project.
    - doc_dir (str): The directory containing MD documentation to embed in the notebook.

    # Returns
    - tuple[str, str]: The script and notebook paths.
    """

    start_time = time.time()

    print(c("Converting source to Jupyter notebook", "bright_blue"))
    print(c("Listing modules", "bright_green"))
    src_files, src_files_to_modules = list_modules(src_dir)

    print(c("Listing documentation", "bright_green"))
    doc_files = list_docs(doc_dir)

    print(c("Ordering modules", "bright_green"))
    sorted_files = topological_sort(src_files, src_files_to_modules)
    for file in sorted_files:
        print(c(src_files_to_modules[file], "white", 1))

    print(c("Cleaning source code", "bright_green"))
    sorted_text_for_files = load_and_clean_files(
        sorted_files, src_files_to_modules)

    print(c("Compiling python script", "bright_green"))
    python_script = compile_python_script(sorted_text_for_files)

    print(c("Creating code cells", "bright_green"))
    cells = compile_code_cells(sorted_text_for_files)
    # at this point, we have all the code cells ready, now we need to add the documentation cells at the right places
    # get all the modules in order, keeping into account removed files and added cells
    cell_modules = [get_module_name_from_cell(cell) for cell in cells]
    # load the text of the documentation files
    # get also the name of the module that the documentation is for
    print(c("Loading documentation", "bright_green"))
    doc_text_for_files = load_doc(doc_files)

    print(c("Ordering documentation", "bright_green"))
    sorted_doc_text_for_files, sorted_doc_files = \
        order_docs(cell_modules, doc_text_for_files, doc_files)

    print(c("Merging code and documentation cells", "bright_green"))
    cells = merge_code_and_doc_cells(
        cells,
        sorted_doc_text_for_files,
        sorted_doc_files,
        cell_modules)

    print(c("Compiling jupyter notebook", "bright_green"))
    jupyter_notebook = compile_notebook(cells)

    
    script_path = f"{output_dir}/colab.py"
    jupyter_path = f"{output_dir}/colab.ipynb"
    print(c(f"Writing script file", "bright_green"))
    with open(script_path, "w") as f:
        f.write(python_script)
    print(c(f"Writing jupyter notebook file", "bright_green"))
    with open(jupyter_path, "w") as f:
        json.dump(jupyter_notebook, f, indent=4)
    print(c(f"Done in {time.time() - start_time:.4f}s", "bright_blue"))
    return script_path, jupyter_path


if __name__ == "__main__":
    src_dir = f"{PROJECT_DIR}/mir"
    doc_dir = f"{PROJECT_DIR}/docs"
    output_dir = f"{DATA_DIR}"
    script, notebook = src_to_ipynb(src_dir, doc_dir, output_dir)
    pwd = os.path.abspath("")
    if script.startswith(pwd):
        script = "." + script[len(pwd):]
    if notebook.startswith(pwd):
        notebook = "." + notebook[len(pwd):]
    print(f"Script: {script}")
    print(f"Notebook: {notebook}")
    
