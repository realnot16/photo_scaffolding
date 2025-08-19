import json
import hashlib
import logging
from pathlib import Path
from tqdm import tqdm
from datetime import datetime

CONFIG_PATH = "config.json"
LOG_FILE = Path("logs/cache_builder.log")

# Logger setup
def setup_logger():
    LOG_FILE.parent.mkdir(exist_ok=True, parents=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def compute_hash(file_path):
    h = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        logging.warning(f"Errore hashing {file_path}: {e}")
        return None

def process_output_dir(output_dir: Path, cache_dir: Path, valid_exts: set):
    total_files = 0
    total_new_hashes = 0
    start_time = datetime.now()

    # Include root + sottocartelle immediate
    all_dirs = [output_dir] + [d for d in output_dir.iterdir() if d.is_dir()]

    for current_dir in all_dirs:
        rel = current_dir.relative_to(output_dir)
        current_cache = cache_dir / rel
        current_cache.mkdir(parents=True, exist_ok=True)
        cache_file = current_cache / "cache.json"

        # Carica cache esistente
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
            except Exception as e:
                logging.warning(f"Errore nel parsing di {cache_file}: {e}")
                cache_data = {"files": {}}
        else:
            cache_data = {"files": {}}

        cached = cache_data.get("files", {})
        new_hashes = 0
        files = [f for f in current_dir.glob("*.*") if f.suffix.lower() in valid_exts]
        total_files += len(files)

        for f in tqdm(files, desc=f"[{rel or output_dir.name}]", unit="file"):
            stat = f.stat()
            if f.name in cached and cached[f.name].get("mtime") == stat.st_mtime:
                continue  # hash valido
            h = compute_hash(f)
            if h:
                cached[f.name] = {
                    "hash": h,
                    "mtime": stat.st_mtime,
                    "size": stat.st_size
                }
                new_hashes += 1

        cache_data["files"] = cached
        cache_data["folder_mtime"] = current_dir.stat().st_mtime
        with cache_file.open("w", encoding="utf-8") as cf:
            json.dump(cache_data, cf, indent=2)

        total_new_hashes += new_hashes
        logging.info(f"{current_dir} → nuovi hash aggiunti: {new_hashes}/{len(files)}")

    duration = (datetime.now() - start_time).total_seconds()
    logging.info(f"\n✅ Totale file analizzati: {total_files}")
    logging.info(f"➕ Totale nuovi hash calcolati: {total_new_hashes}")
    logging.info(f"⏱️ Tempo impiegato: {duration:.2f} secondi")

def main():
    setup_logger()
    cfg = load_config()

    # Foto
    photo_dir = Path(cfg["output"]["foto"])
    photo_cache = Path("cache/foto")
    photo_exts = set(e.lower() for e in cfg["media"]["photo_extensions"])
    logging.info("📸 Aggiorno cache per FOTO")
    process_output_dir(photo_dir, photo_cache, photo_exts)

    # Video
    video_dir = Path(cfg["output"]["video"])
    video_cache = Path("cache/video")
    video_exts = set(e.lower() for e in cfg["media"]["video_extensions"])
    logging.info("\n🎞️ Aggiorno cache per VIDEO")
    process_output_dir(video_dir, video_cache, video_exts)

if __name__ == "__main__":
    main()
