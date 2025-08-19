import os
import shutil
import logging
from pathlib import Path
import json
from tqdm import tqdm

def setup_logger():
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    log_path = logs_dir / "extract_media.log"

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

def is_media_file(file_path, extensions):
    return file_path.suffix.lower() in extensions

def copy_file(src_path, dst_folder):
    dst_folder.mkdir(parents=True, exist_ok=True)
    dest_path = dst_folder / src_path.name
    i = 1
    while dest_path.exists():
        dest_path = dst_folder / f"{src_path.stem}_{i}{src_path.suffix}"
        i += 1
    shutil.copy2(src_path, dest_path)
    logging.info(f"Copiato: {src_path} → {dest_path}")

def scan_and_copy():
    config = load_config()
    source = config["sources"]["initial"]
    output_photo = Path(config["output"]["foto"])
    output_video = Path(config["output"]["video"])

    photo_ext = set(ext.lower() for ext in config["media"]["photo_extensions"])
    video_ext = set(ext.lower() for ext in config["media"]["video_extensions"])

    src_path = Path(source)
    if not src_path.exists():
        logging.error(f"La sorgente '{source}' non esiste.")
        return

    all_files = []

    # Log sottodirectory principali
    for item in src_path.iterdir():
        if item.is_dir():
            logging.info(f"Analizzando la sottodirectory: {item}")

    for file in src_path.rglob("*.*"):
        if file.is_file():
            all_files.append(file)

    logging.info(f"Trovati {len(all_files)} file. Inizio estrazione...")

    for file in tqdm(all_files):
        try:
            if is_media_file(file, photo_ext):
                copy_file(file, output_photo)
            elif is_media_file(file, video_ext):
                copy_file(file, output_video)
        except Exception as e:
            logging.error(f"Errore su {file}: {e}")

if __name__ == "__main__":
    setup_logger()
    scan_and_copy()
