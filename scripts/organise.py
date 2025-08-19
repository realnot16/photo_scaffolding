import os
import json
import shutil
import logging
from pathlib import Path
from tqdm import tqdm
from PIL import Image
import torch
import clip
import face_recognition

# === Logger setup ===
LOG_FILE = Path("log/organizza_foto.log")

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

setup_logger()

# === Caricamento configurazione ===
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

foto_dir = config["output"]["foto"]
output_base = os.path.join("output", "organizzate")
dest_persone = os.path.join(output_base, "Persone")
dest_animali = os.path.join(output_base, "Panorami_Animali")
dest_varie = os.path.join(output_base, "Varie")

os.makedirs(dest_persone, exist_ok=True)
os.makedirs(dest_animali, exist_ok=True)
os.makedirs(dest_varie, exist_ok=True)

# === Caricamento modello CLIP ===
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

etichette = [
    "una persona",
    "più persone",
    "un panorama",
    "un animale",
    "un meme",
    "uno screenshot",
    "una schermata",
    "una foto generica"
]
etichette_tokenizzate = clip.tokenize(etichette).to(device)

# === Funzioni ===
estensioni_valide = tuple(config["media"]["photo_extensions"])

def classifica_clip(immagine_path):
    try:
        image = preprocess(Image.open(immagine_path).convert("RGB")).unsqueeze(0).to(device)
        with torch.no_grad():
            image_features = model.encode_image(image)
            logits_per_image, _ = model(image, etichette_tokenizzate)
            probs = logits_per_image.softmax(dim=-1).cpu().numpy().flatten()
        return etichette[probs.argmax()], probs.max()
    except Exception as e:
        logging.warning(f"Errore nella classificazione di {immagine_path}: {e}")
        return None, 0.0

def contiene_volti(immagine_path):
    try:
        immagine = face_recognition.load_image_file(immagine_path)
        volti = face_recognition.face_locations(immagine)
        return len(volti) > 0
    except Exception as e:
        logging.warning(f"Errore nel rilevamento volti in {immagine_path}: {e}")
        return False

# === Analisi immagini ===
immagini = [f for f in os.listdir(foto_dir) if f.lower().endswith(estensioni_valide)]

for nome_file in tqdm(immagini, desc="Organizzazione immagini"):
    sorgente = os.path.join(foto_dir, nome_file)

    if contiene_volti(sorgente):
        destinazione = os.path.join(dest_persone, nome_file)
        logging.info(f"{nome_file} → Persone (volto rilevato)")
    else:
        etichetta, conf = classifica_clip(sorgente)
        if etichetta in ["un panorama", "un animale"]:
            destinazione = os.path.join(dest_animali, nome_file)
            logging.info(f"{nome_file} → Panorami_Animali ({etichetta} - conf {conf:.2f})")
        else:
            destinazione = os.path.join(dest_varie, nome_file)
            logging.info(f"{nome_file} → Varie ({etichetta} - conf {conf:.2f})")

    try:
        shutil.copy2(sorgente, destinazione)
    except Exception as e:
        logging.warning(f"Errore nella copia di {sorgente} → {destinazione}: {e}")
