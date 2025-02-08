import os
import json
import logging
import time
from pathlib import Path
from dotenv import load_dotenv
from handlers.utils.process_note_paths import load_note_paths, save_note_paths, detect_folder_type

base_path = os.getenv('BASE_PATH')

def process_folder_event(event):
    folder_path = event.get('path')
    action = event.get('action')

    if folder_path.startswith('.') or 'untitled' in folder_path.lower():
        logging.info(f"[INFO] Dossier ignoré : {folder_path}")
        return  # Ignore les dossiers cachés ou non pertinents

    note_paths = load_note_paths()
    relative_path = os.path.relpath(folder_path, base_path)
    relative_path = relative_path
    
    # Vérification pour éviter l'ajout de dossiers vides
    if not relative_path.strip():
        logging.warning(f"[WARNING] Dossier avec un chemin vide détecté et ignoré : {folder_path}")
        return

    logging.debug(f"[DEBUG] relative_path : {relative_path}")

    parts = Path(relative_path).parts
    category = None
    subcategory = None

    folder_type = detect_folder_type(Path(folder_path))

    if action == 'created':
        # Vérifier si la catégorie doit être créée (uniquement si folder_type == storage)
        if folder_type == "storage":
            category = parts[1].lower() if len(parts) > 1 else None
            subcategory = parts[2].lower() if len(parts) > 2 else None
            if category not in note_paths['categories']:
                note_paths['categories'][category] = {
                    "description": f"note about {category}",
                    "prompt_name": "divers",
                    "subcategories": {}
                }
                logging.info(f"[INFO] Catégorie ajoutée : {category}")

            # Ajouter une sous-catégorie si nécessaire
            if subcategory:
                if "subcategories" not in note_paths['categories'][category]:
                    note_paths['categories'][category]["subcategories"] = {}

                if subcategory not in note_paths['categories'][category]['subcategories']:
                    note_paths['categories'][category]['subcategories'][subcategory] = {
                        "description": f"note about {subcategory}",
                        "prompt_name": "divers"
                    }
                    logging.info(f"[INFO] Sous-catégorie ajoutée : {subcategory} dans {category}")

        # Ajouter dans folders (toujours)
        note_paths['folders'][relative_path] = {
            "path": folder_path,
            "category": category,
            "subcategory": subcategory,
            "folder_type": folder_type
        }
        logging.info(f"[INFO] Dossier ajouté : {relative_path}")

    elif action == 'deleted':
        # Attendre un court instant pour éviter les conflits avec Obsidian
        time.sleep(0.5)
        
        # 🔥 Supprimer récursivement tous les sous-dossiers imbriqués avant de supprimer le dossier principal
        subfolders = sorted(
            [key for key in note_paths['folders'] if key.startswith(relative_path + "/")], 
            key=lambda x: -len(x.split('/')) # Trie pour supprimer les plus profonds d'abord
        )
        for subfolder in subfolders:
            try:
                del note_paths['folders'][subfolder]
                logging.info(f"[INFO] Sous-dossier supprimé : {subfolder}")
            except KeyError:
                logging.warning(f"[WARNING] Tentative de suppression d'un sous-dossier inexistant : {subfolder}")

        # Suppression du dossier lui-même
        try:
            if relative_path in note_paths['folders']:
                del note_paths['folders'][relative_path]
                logging.info(f"[INFO] Dossier supprimé : {relative_path}")
        except KeyError:
            logging.warning(f"[WARNING] Tentative de suppression d'un dossier inexistant : {relative_path}")

        # Suppression des sous-catégories uniquement si elles existent
        if category and subcategory:
            try:
                if category in note_paths['categories'] and subcategory in note_paths['categories'][category]['subcategories']:
                    del note_paths['categories'][category]['subcategories'][subcategory]
                    logging.info(f"[INFO] Sous-catégorie supprimée : {subcategory} dans {category}")
                # Vérifier si la catégorie n'a plus de sous-catégories avant de la supprimer
                if not note_paths['categories'][category]['subcategories']:
                    del note_paths['categories'][category]
                    logging.info(f"[INFO] Catégorie supprimée car vide : {category}")
            except KeyError:
                logging.warning(f"[WARNING] Tentative de suppression d'une sous-catégorie inexistante : {subcategory} dans {category}")

        elif category and not subcategory:
            try:
                if category in note_paths['categories'] and not note_paths['categories'][category]['subcategories']:
                    del note_paths['categories'][category]
                    logging.info(f"[INFO] Catégorie supprimée car vide : {category}")
            except KeyError:
                logging.warning(f"[WARNING] Tentative de suppression d'une catégorie inexistante : {category}")

    save_note_paths(note_paths)


def extract_category_subcategory(relative_path):
    parts = relative_path.split(os.sep)
    logging.debug(f"[DEBUG] parts : {parts}")
    if len(parts) >= 3:
        return parts[1], parts[2]  # Première partie = catégorie, deuxième partie = sous-catégorie
    elif len(parts) == 2:
        return parts[1], None  # Seulement une catégorie, pas de sous-catégorie
    return None, None