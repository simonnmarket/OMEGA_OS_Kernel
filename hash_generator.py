import hashlib
import os

def get_sha256(file_path):
    if not os.path.isfile(file_path): return None
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

root = r"C:\OMEGA_PROJETO\PROJETO OMEGA QUANTITATIVE FUND"
files = []
for r, d, f in os.walk(root):
    for name in f:
        full_path = os.path.join(r, name)
        rel_path = os.path.relpath(full_path, root)
        sha = get_sha256(full_path)
        files.append((rel_path, sha))

print("| Arquivo | SHA-256 |")
print("| :--- | :--- |")
for f, s in sorted(files):
    print(f"| {f} | {s} |")
