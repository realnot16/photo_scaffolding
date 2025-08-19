import json
import logging
from pathlib import Path
from collections import defaultdict
from tqdm import tqdm

# Percorsi
CACHE_ROOT = Path("cache/foto")
OUTPUT_ROOT = Path("output/foto")
REPORT_PATH = Path("logs/duplicati_rimossi.txt")

# Logger setup
def setup_logger():
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / "remove_duplicates.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(log_file, encoding='utf-8'), logging.StreamHandler()]
    )

def load_hashes_from_cache(cache_root: Path) -> dict:
    """Carica tutti gli hash da tutte le cache.json."""
    hash_map = defaultdict(list)
    total_files = 0
    total_valid = 0

    cache_files = list(cache_root.rglob("cache.json"))
    for cache_file in cache_files:
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            base_dir = cache_file.parent.relative_to(cache_root)
            for fname, info in data.get("files", {}).items():
                h = info.get("hash")
                if not h:
                    continue
                file_path = OUTPUT_ROOT / base_dir / fname
                if file_path.exists():
                    hash_map[h].append(file_path)
                    total_valid += 1
                total_files += 1
        except Exception as e:
            logging.warning(f"Errore lettura {cache_file}: {e}")

    logging.info(f"Totale file in cache: {total_files}")
    logging.info(f"File validi per l'analisi: {total_valid}")
    logging.info(f"Hash unici: {len(hash_map)}")
    return hash_map

def remove_duplicates():
    hash_map = load_hashes_from_cache(CACHE_ROOT)
    duplicate_log = []

    total_duplicates = 0
    total_hashes_with_duplicates = 0

    for h, files in tqdm(hash_map.items(), desc="Rimozione duplicati"):
        if len(files) > 1:
            keep = files[0]
            to_remove = files[1:]
            removed = 0
            for f in to_remove:
                try:
                    if f.exists():
                        f.unlink()
                        removed += 1
                except Exception as e:
                    logging.warning(f"Impossibile eliminare {f}: {e}")
            if removed > 0:
                total_duplicates += removed
                total_hashes_with_duplicates += 1
                duplicate_log.append(f"{keep.name} | {removed}")

    # Salva report
    REPORT_PATH.parent.mkdir(exist_ok=True, parents=True)
    with REPORT_PATH.open("w", encoding="utf-8") as f:
        for line in duplicate_log:
            f.write(line + "\n")
        f.write(f"\n🔁 Duplicati rimossi: {total_duplicates}\n")
        f.write(f"🔍 Hash con duplicati: {total_hashes_with_duplicates}\n")
        f.write(f"======================================================\n")

    logging.info(f"🔁 Duplicati rimossi: {total_duplicates}")
    logging.info(f"🔍 Hash con duplicati: {total_hashes_with_duplicates}")
    logging.info(f"📄 Report salvato in: {REPORT_PATH}")



if __name__ == "__main__":
    setup_logger()
    remove_duplicates()
