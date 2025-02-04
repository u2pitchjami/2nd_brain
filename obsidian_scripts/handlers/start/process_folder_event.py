import os
import json
import logging
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
    relative_path = "notes/" + relative_path
    logging.debug(f"[DEBUG] relative_path : {relative_path}")
    category, subcategory = extract_category_subcategory(relative_path)
    
    # Utilisation de detect_folder_type pour déterminer le type du dossier
    folder_type = detect_folder_type(Path(folder_path))
    
    # Vérification avant de convertir en minuscules
    category = category.strip().lower() if category else None
    subcategory = subcategory.strip().lower() if subcategory else None
    
    if action == 'created':
        if relative_path not in note_paths:
            note_paths[relative_path] = {
                "category": category,
                "subcategory": subcategory,
                "path": folder_path,
                "prompt_name": "divers",
                "explanation": "note about " + str(category),
                "folder_type": folder_type
            }
            logging.info(f"[INFO] Dossier ajouté : {relative_path}")
    elif action == 'deleted':
        if relative_path in note_paths:
            del note_paths[relative_path]
            logging.info(f"[INFO] Dossier supprimé : {relative_path}")

    save_note_paths(note_paths)

def extract_category_subcategory(relative_path):
    parts = relative_path.split(os.sep)
    logging.debug(f"[DEBUG] parts : {parts}")
    if len(parts) >= 3:
        return parts[1], parts[2]  # Première partie = catégorie, deuxième partie = sous-catégorie
    elif len(parts) == 2:
        return parts[1], None  # Seulement une catégorie, pas de sous-catégorie
    return None, None
