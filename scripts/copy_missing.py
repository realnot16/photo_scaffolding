import shutil
import logging
import json
from pathlib import Path
from tqdm import tqdm

def setup_logger():
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    log_path = logs_dir / "copy_missing.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_missing_list(path):
    results = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) >= 3:
                name = parts[0].strip()
                try:
                    size = int(parts[1].strip())
                    full_path = Path(",".join(parts[2:]).strip())
                    results.append((name, size, full_path))
                except ValueError:
                    continue
    return results

def copy_files_from_missing(missing_file, output_folder, label):
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    files = load_missing_list(missing_file)
    copied = 0
    not_found = 0

    for name, size, src_path in tqdm(files, desc=f"Copia {label.upper()}"):
        if src_path.exists():
            dest = output_folder / src_path.name
            i = 1
            while dest.exists():
                dest = output_folder / f"{src_path.stem}_{i}{src_path.suffix}"
                i += 1
            try:
                shutil.copy2(src_path, dest)
                copied += 1  # Nessun log per copie riuscite
            except Exception as e:
                logging.error(f"❌ Errore copiando {src_path}: {e}")
        else:
            logging.warning(f"⚠️  Non trovato: {src_path}")
            not_found += 1

    print(f"\n📦 Riepilogo copia {label.upper()}:")
    print(f"- Totale da copiare: {len(files)}")
    print(f"- Copiati con successo: {copied}")
    print(f"- Non trovati: {not_found}")
    logging.info(f"\n📦 Riepilogo copia {label.upper()}: {copied} copiati, {not_found} non trovati.")

if __name__ == "__main__":
    setup_logger()
    config = load_config()

    copy_files_from_missing(
        missing_file=config["missing_lists"]["foto"],
        output_folder=config["output"]["foto"],
        label="foto"
    )

    copy_files_from_missing(
        missing_file=config["missing_lists"]["video"],
        output_folder=config["output"]["video"],
        label="video"
    )
