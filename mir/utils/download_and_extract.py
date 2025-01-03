import os
import tarfile
import requests
from tqdm.auto import tqdm

def download_and_extract(url: str, path: str, desc: str = ""):
    stream = requests.get(url, stream=True)
    total_size = int(stream.headers.get('content-length', 0))
    tgz_path = f"{path}.tar.gz"
    output_dir = os.path.dirname(path)
    if not os.path.exists(tgz_path):
        with tqdm(total=total_size, unit='B', unit_scale=True, unit_divisor=1024, desc=f"Downloading {desc}") as pbar:
            with open(tgz_path, 'wb') as f:
                for chunk in stream.iter_content(chunk_size=1024):
                    f.write(chunk)
                    pbar.update(len(chunk))
    with tarfile.open(tgz_path, 'r:gz') as tar:
        members = tqdm([member for member in tar.getmembers() if not os.path.exists(os.path.join(output_dir, member.name))], desc=f"Extracting {desc}")
        tar.extractall(output_dir, members)
            