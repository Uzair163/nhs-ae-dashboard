import csv, os, hashlib
from collections import defaultdict

root = "raw/NHS Data"
groups = defaultdict(list)

for year in sorted(os.listdir(root)):
    ydir = os.path.join(root, year)
    if not os.path.isdir(ydir):
        continue
    for fname in sorted(os.listdir(ydir)):
        if not fname.lower().endswith('.csv'):
            continue
        fpath = os.path.join(ydir, fname)
        with open(fpath, 'rb') as f:
            raw = f.read(2000)
        # strip BOM if present
        text = raw.decode('utf-8-sig', errors='replace')
        header_line = text.split('\r\n')[0].split('\n')[0]
        cols = tuple(c.strip() for c in header_line.split(','))
        key = hashlib.md5(str(cols).encode()).hexdigest()[:8]
        groups[key].append((year, fname, len(cols)))
        groups[key + "_cols"] = cols  # store cols once

print(f"Total files scanned: {sum(len(v) for k,v in groups.items() if not k.endswith('_cols'))}")
print(f"Distinct header signatures: {sum(1 for k in groups if not k.endswith('_cols'))}")
print()
for key in list(groups.keys()):
    if key.endswith('_cols'):
        continue
    files = groups[key]
    cols = groups[key + "_cols"]
    print(f"--- Signature {key} ({len(files)} files, {len(cols)} columns) ---")
    print("Example:", files[0])
    print("Years covered:", sorted(set(y for y,f,n in files)))
    print("Columns:", cols)
    print()
