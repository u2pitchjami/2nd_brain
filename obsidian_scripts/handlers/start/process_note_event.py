import yaml
import shutil
import json
import os
import re
import logging
from datetime import datetime
from pathlib import Path
from handlers.utils.process_note_paths import load_note_paths, save_note_paths
from dotenv import load_dotenv
logger = logging.getLogger()
base_path = os.getenv('BASE_PATH')

def extract_metadata_from_note(note_path):
    """
    Extrait les métadonnées de l'entête YAML d'une note.
    """
    with open(note_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    if content.startswith("---"):
        try:
            yaml_content = content.split('---')[1]
            metadata = yaml.safe_load(yaml_content)
            logging.debug(f"[DEBUG] Métadonnées extraites : {type(metadata)} - {metadata}")
            return {
                "category": metadata.get("category"),
                "subcategory": metadata.get("sub category"),
                "tags": metadata.get("tags", []),
                "status": metadata.get("status", "active"),
                "created": metadata.get("created"),
                "last_modified": metadata.get("last_modified")
            }
        except yaml.YAMLError as e:
            logging.error(f"[ERREUR] Impossible de lire l'entête YAML pour {note_path} : {e}")
    
    return {}

def process_note_event(event):
    global note_paths  # Assure que la variable est globale
    note_paths = load_note_paths()  # Recharge le fichier à chaque événement
    try:
        logging.info(f"[DEBUG] Traitement de l'événement : {event['action']} pour {event['path']}")
        note_paths = load_note_paths()
        note_path = event.get('path')
        action = event.get('action')

        # Vérification de l'existence du fichier
        if not os.path.exists(note_path):
            logging.error(f"[ERREUR] Fichier introuvable : {note_path}")
            return

        # Extraction des métadonnées
        metadata = extract_metadata_from_note(note_path)
        logging.debug(f"[DEBUG] Métadonnées extraites : {metadata}")

        # Construction de la clé pour le JSON
        relative_path = os.path.relpath(note_path, base_path)
        logging.debug(f"[DEBUG] Chemin relatif pour note_paths.json : {relative_path}")

        if action == 'created':
            if relative_path not in note_paths:
                note_paths[relative_path] = {
                    "path": note_path,
                    "category": metadata.get("category"),
                    "subcategory": metadata.get("subcategory"),
                    "tags": metadata.get("tags", []),
                    "status": metadata.get("status", "active"),
                    "created_at": metadata.get("created"),
                    "modified_at": metadata.get("last_modified"),
                    "folder_type": "note"
                }
                logging.info(f"[INFO] Note ajoutée dans note_paths.json : {relative_path}")

        save_note_paths(note_paths)
    except Exception as e:
        logging.error(f"[ERREUR] Erreur lors du traitement de la note : {e}")
