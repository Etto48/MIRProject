import os
import tarfile
import requests
from tqdm.auto import tqdm

def download_and_extract(url: str, path: str):
    stream = requests.get(url, stream=True)
    total_size = int(stream.headers.get('content-length', 0))
    tgz_path = f"{path}.tar.gz"
    output_dir = f"{path}"
    if not os.path.exists(tgz_path):
        with tqdm(total=total_size, unit='B', unit_scale=True, unit_divisor=1024) as pbar:
            with open(tgz_path, 'wb') as f:
                for chunk in stream.iter_content(chunk_size=1024):
                    f.write(chunk)
                    pbar.update(len(chunk))
    if not os.path.exists(output_dir):
        print(f"Extracting {tgz_path} to {output_dir}")
        with tarfile.open(tgz_path, 'r:gz') as tar:
            tar.extractall(output_dir)
            