import urllib.request
import zipfile
import os
import shutil

url = 'https://github.com/VIJNESH200/rrg-indian-sectors/archive/refs/heads/main.zip'
zip_path = 'rrg.zip'
extract_dir = 'integrations/rrg_temp'
target_dir = 'integrations/rrg'

print("Downloading...")
urllib.request.urlretrieve(url, zip_path)
print("Downloaded. Extracting...")

with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_dir)

source_dir = os.path.join(extract_dir, 'rrg-indian-sectors-main')

os.makedirs('integrations', exist_ok=True)
if os.path.exists(target_dir):
    shutil.rmtree(target_dir)

shutil.move(source_dir, target_dir)

os.remove(zip_path)
shutil.rmtree(extract_dir)
print(f"Vendored to {target_dir}")
