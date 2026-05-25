import hashlib, os

def hash_dir(path):
    sha3 = hashlib.sha3_256()
    for root, dirs, files in os.walk(path):
        dirs[:] = sorted([d for d in dirs if d not in [".git", "__pycache__", "venv"]])
        for f in sorted(files):
            if f.endswith((".py", ".json", ".md")):
                fp = os.path.join(root, f)
                try:
                    with open(fp, "rb") as fh:
                        sha3.update(fh.read())
                except OSError:
                    pass
    return sha3.hexdigest()

h = hash_dir(r"C:\OMEGA_QUANTUM_LAB\SOURCE_CODE")
print(f"SHA3 do SOURCE_CODE: {h}")

with open(r"C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\logs\pre_integration_sha3.txt", "w") as f:
    f.write(f"SHA3 SOURCE_CODE pre-nebular-integration: {h}\nData: 2026-04-29\n")

print("SHA3 salvo em: logs/pre_integration_sha3.txt")
