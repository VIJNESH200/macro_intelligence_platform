import urllib.request
import zipfile
import os
import shutil

url = 'https://github.com/VIJNESH200/rrg-indian-sectors/archive/refs/heads/main.zip'
zip_path = 'rrg.zip'
extract_dir = 'integrations/rrg_temp'
target_dir = 'integrations/rrg'

def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    zip_path = os.path.join(repo_root, 'rrg.zip')
    extract_dir = os.path.join(repo_root, 'integrations', 'rrg_temp')
    target_dir = os.path.join(repo_root, 'integrations', 'rrg')

    print("Downloading...")
    urllib.request.urlretrieve(url, zip_path)
    print("Downloaded. Extracting...")

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

    source_dir = os.path.join(extract_dir, 'rrg-indian-sectors-main')

    os.makedirs(os.path.join(repo_root, 'integrations'), exist_ok=True)
    if os.path.exists(target_dir) and target_dir.endswith('integrations/rrg'):
        shutil.rmtree(target_dir)

    shutil.move(source_dir, target_dir)

    if os.path.exists(zip_path):
        os.remove(zip_path)
    if os.path.exists(extract_dir) and extract_dir.endswith('integrations/rrg_temp'):
        shutil.rmtree(extract_dir)
    print(f"Vendored to {target_dir}")


if __name__ == '__main__':
    main()
