import logging
import json
from pathlib import Path
from tqdm import tqdm
from hashlib import sha256

CONFIG_PATH = "config.json"
CACHE_ROOT = Path("cache")

# Logger setup
def setup_logger():
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / "find_missing.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(log_file, encoding='utf-8'), logging.StreamHandler()]
    )

def load_config(path=CONFIG_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def index_name_size(folder: Path, valid_exts: set) -> dict:
    index = {}
    for file in folder.rglob("*"):
        if file.is_file() and file.suffix.lower() in valid_exts:
            key = (file.name.lower(), file.stat().st_size)
            index[key] = file
    return index

def get_file_hash(path: Path, block_size: int = 65536) -> str:
    sha = sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(block_size), b''):
            sha.update(chunk)
    return sha.hexdigest()

def load_hash_cache_for_folder(output_root: Path, valid_exts: set) -> dict:
    hashes = {}
    for cache_file in (CACHE_ROOT / output_root.name).rglob("cache.json"):
        rel = cache_file.parent.relative_to(CACHE_ROOT / output_root.name)
        out_dir = output_root / rel
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception as e:
            logging.warning(f"Could not read cache {cache_file}: {e}")
            continue
        if not out_dir.exists():
            logging.warning(f"Output subdir missing: {out_dir}, cache ignored.")
            continue
        folder_mtime_actual = out_dir.stat().st_mtime
        if abs(folder_mtime_actual - data.get("folder_mtime", -1)) > 1:
            logging.warning(f"Cache outdated for {out_dir}")
            continue
        for fname, info in data.get("files", {}).items():
            h = info.get("hash")
            if h and fname.lower().endswith(tuple(valid_exts)):
                file_path = out_dir / fname
                if file_path.exists():
                    hashes[h] = file_path
    return hashes

def verify_cache_mtime(output_folder: Path, cache_root: Path) -> bool:
    cache_file = cache_root / "cache.json"
    if not cache_file.exists():
        logging.warning(f"Nessuna cache trovata in: {cache_file}")
        return False
    try:
        with cache_file.open("r", encoding="utf-8") as f:
            cache_data = json.load(f)
    except Exception as e:
        logging.error(f"Errore lettura cache: {e}")
        return False
    if "folder_mtime" not in cache_data:
        logging.warning("Cache invalida: manca 'folder_mtime'")
        return False
    folder_mtime = output_folder.stat().st_mtime
    if abs(cache_data["folder_mtime"] - folder_mtime) > 1:
        logging.warning("⚠️ La cartella di output è stata modificata dopo la creazione della cache.")
        return False
    return True

def find_missing(sources, output_folder, valid_exts, missing_file, label, tolerance, mode):
    out_folder = Path(output_folder)
    if not out_folder.exists():
        logging.error(f"La cartella di output non esiste: {out_folder}")
        return

    for src in sources:
        if not Path(src).exists():
            logging.error(f"La cartella di origine non esiste: {src}")
            return

    cache_path = Path(f"cache/{label}/cache.json")
    if mode == 'hash' and not verify_cache_mtime(out_folder, cache_path.parent):
        logging.warning(f"⚠️ Cache non valida o outdated per '{label}'.")
        choice = input("Procedere con la ricerca usando solo nome e dimensione? (s/n): ").strip().lower()
        if choice != 's':
            logging.info("Operazione annullata dall'utente.")
            return
        mode = 'name'

    logging.info(f"\n=== Analisi '{label}' (mode={mode}) ===")
    name_index = index_name_size(out_folder, valid_exts)
    hash_index = {}

    if mode == 'hash':
        hash_index = load_hash_cache_for_folder(out_folder, valid_exts)
        logging.info(f"Loaded {len(hash_index)} hashes from cache for {label}")

    missing = []
    for src in sources:
        src_folder = Path(src)
        logging.info(f"Scanning source: {src_folder}")
        for file in tqdm(src_folder.rglob("*"), desc=f"{label} -> {src_folder}"):
            if not file.is_file() or file.suffix.lower() not in valid_exts:
                continue
            name = file.name
            size = file.stat().st_size
            key = (name.lower(), size)
            if key in name_index:
                continue
            if mode == 'hash':
                try:
                    h = get_file_hash(file)
                except Exception as e:
                    logging.warning(f"Errore hashing {file}: {e}")
                    missing.append((name, size, str(file)))
                    continue
                if h in hash_index:
                    continue
            missing.append((name, size, str(file)))

    Path(missing_file).parent.mkdir(parents=True, exist_ok=True)
    with open(missing_file, 'w', encoding='utf-8') as f:
        for name, size, path in missing:
            f.write(f"{name},{size},{path}\n")

    logging.info(f"{label}: totali output = {len(name_index)} / hash disponibili = {len(hash_index)} / file mancanti = {len(missing)}")
    logging.info(f"Report saved to: {missing_file}")

def main():
    setup_logger()
    cfg = load_config()
    print("1: name+size, 2: name+size+hash fallback")
    m = input("Choose mode (1/2): ").strip()
    mode = 'name' if m == '1' else 'hash'
    tol = cfg['media'].get('size_tolerance_bytes', 0)

    find_missing(
        sources=cfg['sources'].get('altre_foto', []),
        output_folder=cfg['output']['foto'],
        valid_exts=set(cfg['media']['photo_extensions']),
        missing_file=cfg['missing_lists']['foto'],
        label='foto',
        tolerance=tol,
        mode=mode
    )

    find_missing(
        sources=cfg['sources'].get('altro_video', []),
        output_folder=cfg['output']['video'],
        valid_exts=set(cfg['media']['video_extensions']),
        missing_file=cfg['missing_lists']['video'],
        label='video',
        tolerance=tol,
        mode=mode
    )

if __name__ == '__main__':
    main()
