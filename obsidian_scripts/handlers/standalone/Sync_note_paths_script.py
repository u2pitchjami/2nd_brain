import os
from dotenv import load_dotenv


# Chemin dynamique basé sur le script en cours
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env")
# Charger le fichier .env
load_dotenv(env_path)
from handlers.logger_setup import setup_logging # noqa: C0413
setup_logging()
import json
from pathlib import Path
import logging
from handlers.utils.process_note_paths import load_note_paths, save_note_paths, detect_folder_type, categ_extract
from handlers.start.process_folder_event import extract_category_subcategory
base_path = os.getenv('BASE_PATH')

excluded_dirs = ['.git', 'node_modules', '__pycache__']

def sync_note_paths():
    note_paths = load_note_paths()
    logging.info(f"[INFO] Synchronisation des dossiers dans {base_path}")

    for root, dirs, _ in os.walk(base_path):
        for folder in dirs:
            logging.info(f"[INFO] folder {folder}")
            if is_excluded(folder):
                logging.debug(f"[DEBUG] Dossier exclu : {folder}")
                continue

            folder_path = Path(root) / folder
            relative_path = os.path.relpath(folder_path, base_path)
            category, subcategory = extract_category_subcategory(relative_path)
            folder_type = detect_folder_type(folder_path)

            dict_key = generate_dict_key(relative_path)

            # Mettre à jour si le dossier existe déjà avec des données différentes
            if dict_key in note_paths:
                existing_data = note_paths[dict_key]
                if existing_data.get("folder_type") != folder_type:
                    logging.info(f"[INFO] Mise à jour du type de dossier : {dict_key} en {folder_type}")
                    note_paths[dict_key]["folder_type"] = folder_type
            else:
                note_paths[dict_key] = {
                    "category": category.lower() if category else "",
                    "subcategory": subcategory.lower() if subcategory else "",
                    "path": str(folder_path),
                    "prompt_name": "divers",
                    "explanation": f"Note about {subcategory or category}",
                    "folder_type": folder_type
                }
                logging.info(f"[INFO] Dossier ajouté : {dict_key} avec type {folder_type}")

    save_note_paths(note_paths)
    logging.info("[INFO] Synchronisation terminée.")

# Vérifier si le dossier doit être exclu
def is_excluded(folder_name):
    return any(excluded in folder_name for excluded in excluded_dirs)

# Générer la clé du dictionnaire avec la structure correcte
def generate_dict_key(relative_path):
    return f"notes/{relative_path}"

def clean_note_paths():
    note_paths = load_note_paths()
    cleaned_note_paths = {key: value for key, value in note_paths.items()
                          if '.obsidian' not in key and '.trash' not in key and '.sav' not in key and '.smart-env' not in key and key.startswith('notes/')}

    if len(cleaned_note_paths) != len(note_paths):
        logging.info("[INFO] Entrées indésirables supprimées de note_paths.json")
        save_note_paths(cleaned_note_paths)
    else:
        logging.info("[INFO] Aucun nettoyage n'était nécessaire dans note_paths.json")
  
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sync_note_paths()
    clean_note_paths()  # Pour nettoyer les entrées indésirables