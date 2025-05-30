# handlers/utils/note_index.py

import json
from pathlib import Path
import os
import logging
_note_index_cache = None

# Utilisation de _note_index_cache pour l'index des notes
def load_note_index():
    global _note_index_cache
    note_paths_file = os.getenv('NOTE_PATHS_FILE')
    logging.debug(f"[DEBUG] Tentative de chargement de l'index depuis : {note_paths_file}")

    if _note_index_cache:
        logging.debug(f"[DEBUG] Cache d'index existant détecté. Utilisation de l'index en mémoire.")
        return _note_index_cache  # Retourne directement l'index en cache
    logging.debug(f"[DEBUG] Test")
    try:
        with open(note_paths_file, 'r', encoding='utf-8') as file:
            
            data = json.load(file)
            logging.debug(f"[DEBUG] load_note_index : {data}")
            notes = data.get('notes', {})
            logging.debug(f"[DEBUG] load_note_index : {notes}")
            # Ajout de logs pour vérifier le format des notes
            for note_path, note_data in notes.items():
                logging.debug(f"[DEBUG] Type de note_path : {type(note_path)} - note_path : {note_path}")
    
                if 'title' not in note_data:
                    logging.error(f"[ERREUR] La note à l'emplacement {note_path} n'a pas de champ 'title'. Données : {note_data}")
                else:
                    logging.debug(f"[DEBUG] Note trouvée : {note_data['title']} (path: {note_path})")

            _note_index_cache = {
                note_data['title']: str(note_path)
                for note_path, note_data in notes.items()
                if note_data.get("status") == "synthesis"  # Sélectionne uniquement les notes de statut "synthesis"
            }
            logging.debug(f"[DEBUG] Test2_note_index_cache {(_note_index_cache)}")
            
            #logging.debug(f"[DEBUG] Index chargé avec succès : {_note_index_cache.keys()}")
            return _note_index_cache
    except FileNotFoundError:
        logging.error(f"[ERREUR] Fichier introuvable : {note_paths_file}")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"[ERREUR] Problème de décodage JSON dans {note_paths_file}: {e}")
        return {}



def update_note_index(note_title, note_key):
    """
    Met à jour l'index avec une nouvelle note
    """
    global _note_index_cache
    if _note_index_cache is None:
        load_note_index()
    _note_index_cache[note_title] = note_key

def remove_note_from_index(note_title):
    """
    Supprime une note de l'index
    """
    global _note_index_cache
    if _note_index_cache and note_title in _note_index_cache:
        del _note_index_cache[note_title]
