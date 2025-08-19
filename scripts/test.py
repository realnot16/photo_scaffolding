import json
from pathlib import Path

# Carica la cache
cache = json.load(open("hash_index_output.json", "r", encoding="utf-8"))
cached = cache.get("__meta__", {}).get("folder_mtime", None)
print("mtime salvato in cache:   ", cached)

# Prendi il mtime reale della directory
actual = Path("output/video").stat().st_mtime
print("mtime reale della dir:    ", actual)

if cached == actual:
    print("✅ OK: i due valori coincidono")
else:
    print("⚠️ Non coincidono: cache→dir ha cambiato qualcosa?")