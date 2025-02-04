"""
gestion de note_paths.
"""
import shutil
import json
import os
import re
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Variables de cache pour éviter des rechargements inutiles
_note_paths_cache = None
_last_modified_time = None

def load_note_paths(force_reload=False):
    """
    charge le dictionnaire note_paths.
    """
    note_paths_file = os.getenv('NOTE_PATHS_FILE')
    global _note_paths_cache, _last_modified_time
    #logging.debug(f"[DEBUG] Contenu de note_paths.json : {type(note_paths)} - {note_paths}")
    #logging.debug(f"[DEBUG] Contenu de note_paths.json : {type(_note_paths_cache)} - {_note_paths_cache}")
    
    
    if force_reload:
        logging.info("[INFO] Rechargement forcé de note_paths.json.")
        _note_paths_cache = None
        _last_modified_time = None  # Remettre à zéro le timestamp pour forcer le rechargement
 
    
    
    try:
        current_modified_time = os.path.getmtime(note_paths_file)
        
        # Recharge le fichier seulement s'il a été modifié
        if _note_paths_cache is None or _last_modified_time != current_modified_time:
            with open(note_paths_file, 'r') as f:
                _note_paths_cache = json.load(f)
                _last_modified_time = current_modified_time
                logging.info("[INFO] note_paths.json rechargé suite à une modification.")
        else:
            logging.debug("[DEBUG] note_paths.json inchangé, pas de rechargement.")
            
        #logging.debug(f"[DEBUG] Contenu de note_paths.json : {type(note_paths)} - {note_paths}")
        logging.debug(f"[DEBUG] Contenu de note_paths.json : {type(_note_paths_cache)} - {_note_paths_cache}")
        return _note_paths_cache
    
    except FileNotFoundError:
        logging.error("[ERREUR] Le fichier %s est introuvable.", note_paths_file)
        return {}

def get_path_by_category_and_subcategory(category, subcategory):
    """
    lit le path à partir des variabls categs
    """
    note_paths = load_note_paths()
    for _, value in note_paths.items():
        if value.get("category") == category and value.get("subcategory") == subcategory:
            return Path(value.get("path"))  # Conversion directe en Path
    return None  # Retourne None si aucune correspondance n'est trouvée

# Récupérer un chemin existant
def get_path_from_classification(category, subcategory):
    """
    Récupérer un chemin existant par categ et sous categ
    """
    logging.debug("[DEBUG] get_path_from_classification : %s %s", category, subcategory)
    note_paths = load_note_paths()
    
    for details in note_paths.values():
        if details.get("folder_type") != "storage":
            continue  # Ignore les dossiers techniques
        
        if details["category"] == category and details["subcategory"] == subcategory:
            logging.debug("[DEBUG] Correspondance trouvée : %s", details["path"])
            return Path(details["path"])
    raise KeyError(
        f"Aucune correspondance trouvée pour catégorie {category} et sous-catégorie {subcategory}")
    
def save_note_paths(note_paths):
    """
    Sauvegarde le dictionnaire NOTE_PATHS dans un fichier JSON.
    """
    note_paths_file = os.getenv('NOTE_PATHS_FILE')
    data = {
        key: {
            **value,
            "path": str(value["path"])  # Convert Path en chaîne
        } for key, value in note_paths.items()
    }
    with open(note_paths_file, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    logging.info("Fichier JSON %s mis à jour avec succès.")

def categ_extract(base_folder):
    """
    Extrait la catégorie et sous-catégorie de la note par l'emplacement.
    """
    logging.debug("entrée categ_extract pour : %s", base_folder)
    logging.debug("entrée categ_extract type: %s", type(base_folder))
    note_paths = load_note_paths()
    base_folder_str = str(base_folder)  # Convertir en string pour comparaison

    try:
        for path, details in note_paths.items():
            logging.debug("[DEBUG] path : %s", path)
            if str(details["path"]) in base_folder_str:
                logging.debug("[DEBUG] Traitement de la note pour : %s", details['path'])
                category = details["category"]
                subcategory = details.get("subcategory")
                logging.debug("[DEBUG] categ extract : %s / %s", category, subcategory)
        return category, subcategory
    except ValueError:
        logging.error("Catégorie introuvable pour %s", base_folder)
        raise

    logging.warning("[WARN] Aucun chemin correspondant trouvé pour : %s", base_folder)
    return None, None  # Évite un crash si aucune catégorie n'est trouvée

def is_folder_included(path, include_types=None, exclude_types=None):
    """
    Vérifie si un dossier est inclus en fonction des types spécifiés.
    
    :param path: Chemin à vérifier.
    :param note_paths: Dictionnaire des chemins (chargé depuis note_paths.json).
    :param include_types: Types à inclure (par exemple : ['storage']).
    :param exclude_types: Types à exclure (par exemple : ['technical']).
    :return: True si le dossier est à inclure, False sinon.
    """
    logging.debug("[DEBUG] is_folder_included")
    note_paths = load_note_paths()
    path_obj = Path(path).resolve()  # Normalise le chemin
    logging.debug(f"[DEBUG] is_folder_included path_obj: {path_obj}")

    for details in note_paths.values():
        folder_type = details.get('folder_type', 'storage')
        folder_path_obj = Path(details['path']).resolve()
        logging.debug(f"[DEBUG] is_folder_included folder_path_obj: {folder_path_obj}")

        # Vérifie si le chemin correspond à un dossier dans note_paths.json
        if path_obj == folder_path_obj:
            # Vérifie les exclusions
            if exclude_types and folder_type in exclude_types:
                logging.debug(f"[DEBUG] Dossier exclu : {path} (type : {folder_type})")
                return False
            # Vérifie les inclusions
            if include_types and folder_type not in include_types:
                logging.debug(f"[DEBUG] Dossier non inclus : {path} (type : {folder_type})")
                return False
            # Si tout est bon, le dossier est inclus
            logging.debug(f"[DEBUG] Dossier inclus : {path} (type : {folder_type})")
            return True

    # Si le chemin n'est pas dans note_paths.json, on l'exclut par défaut
    logging.debug(f"[DEBUG] Chemin non trouvé dans note_paths.json : {path}")
    return False

def filter_folders_by_type(include_types=None, exclude_types=None):
    """
    Filtre les dossiers de note_paths.json en fonction des types inclus ou exclus.
    
    :param note_paths: Dictionnaire des chemins (chargé depuis note_paths.json).
    :param include_types: Liste des types de dossiers à inclure (ex: ['storage', 'archive']).
    :param exclude_types: Liste des types de dossiers à exclure (ex: ['technical']).
    :return: Liste des chemins correspondant aux critères.
    """
    note_paths = load_note_paths()
    filtered_paths = []

    for details in note_paths.values():
        folder_type = details.get('folder_type', 'storage')  # Par défaut, 'storage' si non défini

        # Si des types à inclure sont spécifiés
        if include_types and folder_type not in include_types:
            continue  # Ignore les dossiers qui ne sont pas dans les types inclus
        
        # Si des types à exclure sont spécifiés
        if exclude_types and folder_type in exclude_types:
            continue  # Ignore les dossiers à exclure
        
        filtered_paths.append(details['path'])
    
    return filtered_paths

           
def get_prompt_name(category, subcategory):
    """
    Récupère le nom du prompt basé sur la catégorie et la sous-catégorie de manière sécurisée.
    """
    note_paths = load_note_paths()
    logging.debug(f"[DEBUG] get_prompt_name category {category}, subcategory {subcategory}, note_paths {note_paths}")
    for details in note_paths.values():
        # Vérifie que les clés nécessaires existent avant de comparer
        if details.get("category") == category and details.get("subcategory") == subcategory:
            return details.get("prompt_name", None)
    return None  # Retourne None si aucune correspondance

# Détecter le type de dossier
def detect_folder_type(folder_path):
    if 'Archives' in folder_path.parts:
        return 'archive'
    elif 'Z_technical' in folder_path.parts:
        return 'technical'
    else:
        return 'storage'


