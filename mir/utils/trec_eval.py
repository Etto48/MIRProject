import git
import os
import subprocess

from mir import DATA_DIR

def get_trec_eval(verbose: bool = False, force: bool = False) -> str:
    """
    Downloads and builds trec_eval from the official repository.
    Returns the path to the built executable.
    If force is True, the executable will be rebuilt even if it already exists.
    """
    if os.name == "nt":
        executable_path = f"{DATA_DIR}/trec_eval/trec_eval.exe"
    else:
        executable_path = f"{DATA_DIR}/trec_eval/trec_eval"
        
    # skip build if executable already exists
    if os.path.exists(executable_path) and not force:
        return executable_path
    
    if os.path.exists(f"{DATA_DIR}/trec_eval"):
        if verbose:
            print("Updating trec_eval")
        git.Git(f"{DATA_DIR}/trec_eval").pull()
    else:
        if verbose:
            print("Cloning trec_eval")
        git.Repo.clone_from(
            "https://github.com/usnistgov/trec_eval",
            f"{DATA_DIR}/trec_eval")
    if verbose:
        print("Downloading trec_eval submodules")
    git.Git(f"{DATA_DIR}/trec_eval")\
        .submodule("update", "--init", "--recursive")
    if verbose:
        print("Building trec_eval")
    if os.name == "nt":
        VS_DEV_CMD = "C:\\Program Files\\Microsoft Visual Studio\\2022\\Community\\Common7\\Tools\\VsDevCmd.bat"
        if not os.path.exists(VS_DEV_CMD):
            raise FileNotFoundError(
                "VsDevCmd.bat not found. Make sure you have Visual Studio 2022 installed.")
        batch_path = f"{DATA_DIR}/trec_eval/build.bat"
        cmd = f"\"{VS_DEV_CMD}\" & \"{batch_path}\""
        subprocess.run(
            cmd, cwd=f"{DATA_DIR}/trec_eval", 
            stdout=None if verbose else subprocess.DEVNULL,
            stderr=None if verbose else subprocess.DEVNULL
        ).check_returncode()
    else:
        subprocess.run(
            "make", cwd=f"{DATA_DIR}/trec_eval",
            stdout=None if verbose else subprocess.DEVNULL,
            stderr=None if verbose else subprocess.DEVNULL
        ).check_returncode()
    if not os.path.exists(executable_path):
        raise FileNotFoundError("trec_eval executable not found.")
    if verbose:
        print("trec_eval build completed.")
    return executable_path

if __name__ == "__main__":
    executable = get_trec_eval(verbose=True)
    subprocess.run([executable, "-h"])
