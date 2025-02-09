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
from handlers.utils.normalization import normalize_path
import threading
from fasteners import InterProcessLock

# Variables de cache pour éviter des rechargements inutiles
_note_paths_cache = None
_last_modified_time = None
_save_lock = threading.Lock()  # 🔒 Verrou interne au programme
lock = InterProcessLock(os.getenv('NOTE_PATHS_FILE') + ".lock")  # 🔒 Verrou pour protéger entre plusieurs processus

def load_note_paths(force_reload=False):
    """
    Charge `note_paths.json` avec gestion du cache et correction automatique.
    """

    global _note_paths_cache, _last_modified_time
    note_paths_file = os.getenv('NOTE_PATHS_FILE')

    logging.debug(f"[DEBUG] Tentative de chargement de `note_paths.json` par {threading.current_thread().name}")
    
    # ✅ Vérifie si on peut utiliser le cache AVANT d’accéder au fichier
    current_modified_time = os.path.getmtime(note_paths_file)
    if not force_reload and _note_paths_cache is not None and _last_modified_time == current_modified_time:
        logging.debug("[DEBUG] `note_paths.json` inchangé, utilisation du cache.")
        return _note_paths_cache

    try:
        logging.info("[INFO] Chargement de `note_paths.json` (modification détectée ou cache vide).")
        with open(note_paths_file, 'r', encoding='utf-8') as f:
            try:
                note_paths = json.load(f)
            except json.JSONDecodeError as e:
                logging.error("[ERREUR] `note_paths.json` corrompu : %s", e)
                note_paths = {}  # 🔄 Retourne un JSON vide en cas de corruption

        note_paths = sanitize_note_paths(note_paths)
        logging.debug("[DEBUG] `note_paths.json` sortie sanitize.")

        # ✅ `save_note_paths()` gère maintenant `_save_lock`, donc pas de verrou ici
        save_note_paths(note_paths)

        _note_paths_cache = note_paths
        _last_modified_time = current_modified_time
        logging.info("[INFO] `note_paths.json` chargé, validé et cache mis à jour.")

        return note_paths

    except FileNotFoundError:
        logging.warning("[WARNING] `note_paths.json` introuvable, création d'un fichier vide.")
        return {"categories": {}, "folders": {}, "notes": {}}




def get_path_by_category_and_subcategory(category, subcategory):
    """
    Récupère le chemin du dossier correspondant à une catégorie et sous-catégorie.
    """
    note_paths = load_note_paths()

    # Vérifier si la catégorie existe dans le dictionnaire
    category_data = note_paths.get("categories", {}).get(category.lower())
    if not category_data:
        logging.warning(f"[WARN] Catégorie '{category}' non trouvée.")
        return None

    # Vérifier si la sous-catégorie existe (si elle est spécifiée)
    if subcategory:
        subcategory_data = category_data.get("subcategories", {}).get(subcategory.lower())
        if not subcategory_data:
            logging.warning(f"[WARN] Sous-catégorie '{subcategory}' non trouvée dans '{category}'.")
            return None

    # Chercher le dossier correspondant dans 'folders'
    for folder_key, folder_data in note_paths.get("folders", {}).items():
        if folder_data.get("category") == category and folder_data.get("subcategory") == subcategory:
            return Path(folder_data.get("path"))

    logging.warning(f"[WARN] Aucun dossier trouvé pour {category}/{subcategory}.")
    return None
# Récupérer un chemin existant
def get_path_from_classification(category, subcategory):
    """
    Récupérer un chemin existant par catégorie et sous-catégorie.
    """
    logging.debug("[DEBUG] get_path_from_classification : %s %s", category, subcategory)
    note_paths = load_note_paths()
    
    # Recherche dans les dossiers de note_paths.json
    for folder_key, details in note_paths.get("folders", {}).items():
        if details.get("folder_type") != "storage":
            continue  # Ignore les dossiers techniques
        
        if details.get("category") == category and details.get("subcategory") == subcategory:
            logging.debug("[DEBUG] Correspondance trouvée : %s", details["path"])
            return Path(details["path"])
    
    raise KeyError(
        f"Aucune correspondance trouvée pour catégorie {category} et sous-catégorie {subcategory}")
    
def save_note_paths(note_paths):
    """Sauvegarde sécurisée de note_paths.json avec relecture avant écriture pour éviter les écrasements."""
    logging.debug("[DEBUG] entrée save_note_paths")
    logging.debug(f"[DEBUG] Tentative d'acquisition de _save_lock par {threading.current_thread().name}")

    note_paths_file = os.getenv('NOTE_PATHS_FILE')
    temp_file = note_paths_file + ".tmp"

    if not _save_lock.acquire(timeout=30):
        logging.error("[ERREUR] ⏳ _save_lock bloqué trop longtemps dans `save_note_paths()`, abandon")
        return

    try:
        logging.debug(f"[DEBUG] 🔒 _save_lock acquis par {threading.current_thread().name} dans `save_note_paths()`")

        with lock:
            try:
                # 🔄 Relecture du fichier pour éviter d'écraser les modifs d'un autre process
                if os.path.exists(note_paths_file):
                    with open(note_paths_file, "r", encoding="utf-8") as f:
                        latest_data = json.load(f)
                        logging.debug("[DEBUG] Dernière version de note_paths chargée depuis le fichier.")

                    # 🔄 Fusion des nouvelles données avec les existantes
                    for key, value in note_paths["notes"].items():
                        latest_data["notes"][key] = value

                    for key, value in note_paths["folders"].items():
                        latest_data["folders"][key] = value

                    note_paths = latest_data  # On travaille avec la version fusionnée

                # 🔹 Normalisation des chemins avant la sauvegarde
                normalized_notes = {normalize_path(k): v for k, v in note_paths["notes"].items()}
                normalized_folders = {normalize_path(k): v for k, v in note_paths["folders"].items()}

                note_paths["notes"] = normalized_notes
                note_paths["folders"] = normalized_folders

                # 🔥 Écriture dans un fichier temporaire
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(note_paths, f, indent=4, ensure_ascii=False)

                # 🔄 Remplacement atomique
                os.replace(temp_file, note_paths_file)

                logging.debug(f"[DEBUG] Après normalisation, {len(note_paths['notes'])} notes enregistrées.")
                logging.info("[INFO] `note_paths.json` mis à jour avec normalisation et protection contre corruption.")

            except Exception as e:
                logging.error(f"[ERREUR] Impossible de sauvegarder `note_paths.json` : {e}")

    finally:
        _save_lock.release()
        logging.debug(f"[DEBUG] 🔓 _save_lock libéré par {threading.current_thread().name} dans `save_note_paths()`")



def categ_extract(base_folder):
    """
    Extrait la catégorie et sous-catégorie d'une note selon son emplacement.
    """
    logging.debug("entrée categ_extract pour : %s", base_folder)
    logging.debug("entrée categ_extract type: %s", type(base_folder))
    note_paths = load_note_paths()
    base_folder = Path(base_folder)  # ✅ Assure que `base_folder` est bien un Path

    # Vérifier dans la section des dossiers
    for folder_path, folder_details in note_paths.get("folders", {}).items():
        folder_abs_path = Path(folder_details["path"])  # 🔹 Normalisation en Path

        if folder_abs_path == base_folder:  # 🔥 Vérification avec Path()
            category = folder_details.get("category")
            subcategory = folder_details.get("subcategory")
            logging.debug("[DEBUG] Dossier trouvé - Catégorie: %s, Sous-catégorie: %s", category, subcategory)
            return category, subcategory

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

    folders = note_paths.get('folders', {})

    for folder_key, details in folders.items():
        folder_type = details.get('folder_type', 'storage')
        folder_path_obj = Path(details['path']).resolve()
        logging.debug(f"[DEBUG] Vérification dossier : {folder_path_obj} (type : {folder_type})")

        if path_obj == folder_path_obj:
            if exclude_types and folder_type in exclude_types:
                logging.debug(f"[DEBUG] Dossier exclu : {path} (type : {folder_type})")
                return False
            if include_types and folder_type not in include_types:
                logging.debug(f"[DEBUG] Dossier non inclus : {path} (type : {folder_type})")
                return False
            
            logging.debug(f"[DEBUG] Dossier inclus : {path} (type : {folder_type})")
            return True

    logging.debug(f"[DEBUG] Dossier non trouvé dans note_paths.json : {path}")
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
    folders = note_paths.get("folders", {})

    filtered_paths = []
    for folder_path, details in folders.items():
        folder_type = details.get("folder_type", "storage")

        if include_types and folder_type not in include_types:
            continue
        if exclude_types and folder_type in exclude_types:
            continue

        filtered_paths.append(details["path"])

    return filtered_paths


           
def get_prompt_name(category, subcategory):
    """
    Récupère le nom du prompt basé sur la catégorie et la sous-catégorie de manière sécurisée.
    """
    note_paths = load_note_paths()
    categories = note_paths.get("categories", {})

    category_info = categories.get(category, {})
    subcategories = category_info.get("subcategories", {})

    if subcategory in subcategories:
        return subcategories[subcategory].get("prompt_name", None)

    return category_info.get("prompt_name", None)  # Retourne celui de la catégorie si aucun pour la sous-catégorie


# Détecter le type de dossier
def detect_folder_type(folder_path):
    if 'Archives' in folder_path.parts:
        return 'archive'
    elif 'Z_technical' in folder_path.parts:
        return 'technical'
    elif 'Z_Storage' in folder_path.parts:
        return 'storage'
    elif 'Personnal' in folder_path.parts:
        return 'personnal'
    elif 'Projects' in folder_path.parts:
        return 'project'
    elif 'Todo' in folder_path.parts:
        return 'todo'
    else:
        return None


def debug_note_paths():
    """
    Affiche des logs détaillés sur la structure de `note_paths.json` pour le debug.
    """
    note_paths = load_note_paths()
    logging.debug("[DEBUG] Vérification de `note_paths.json`")
    
    logging.debug("[DEBUG] Type de `categories`: %s", type(note_paths.get("categories")))
    logging.debug("[DEBUG] Type de `folders`: %s", type(note_paths.get("folders")))
    logging.debug("[DEBUG] Type de `notes`: %s", type(note_paths.get("notes")))

    if "categories" in note_paths and isinstance(note_paths["categories"], dict):
        for category, details in note_paths["categories"].items():
            logging.debug("[DEBUG] Catégorie : %s - Type: %s", category, type(details))

    if "folders" in note_paths and isinstance(note_paths["folders"], dict):
        for folder, details in note_paths["folders"].items():
            logging.debug("[DEBUG] Folder : %s - Path: %s", folder, details.get("path", "N/A"))

def sanitize_note_paths(note_paths):
    """
    Vérifie et corrige les erreurs dans note_paths.json.
    - S'assure que `folders`, `categories` et `notes` sont bien des dictionnaires.
    - Supprime les entrées avec `path: ""`
    - Loggue les corrections effectuées
    """
    logging.info("[INFO] Vérification et correction de `note_paths.json`")

    # 🔍 Vérification que les sections principales sont bien des dicts
    for key in ["categories", "folders", "notes"]:
        if key not in note_paths or not isinstance(note_paths[key], dict):
            logging.error("[ERREUR] `%s` est invalide dans note_paths.json ! Réinitialisation.", key)
            note_paths[key] = {}  # Correction automatique en dict vide
    logging.debug("[DEBUG] Vérification des clés principales terminée.")
    # 🔍 Vérification que chaque entrée dans `folders` est bien un dict
    folders_to_delete = []
    for key, value in list(note_paths["folders"].items()):
        if not isinstance(value, dict):
            logging.error("[ERREUR] Entrée invalide dans `folders`: %s (type: %s)", key, type(value))
            folders_to_delete.append(key)
    logging.debug("[DEBUG] Suppression des dossiers invalides terminée.")

    # Suppression des entrées invalides
    for folder in folders_to_delete:
        logging.warning("[WARNING] Suppression d'un folder invalide : %s", folder)
        del note_paths["folders"][folder]
    logging.debug("[DEBUG] Suppression des dossiers avec path vide terminée.")
    # 🔍 Suppression des entrées `path: ""`
    folders_to_delete = [key for key, value in note_paths["folders"].items() if value.get("path") == ""]
    for folder in folders_to_delete:
        logging.warning("[WARNING] Suppression d'une entrée folder avec path vide : %s", folder)
        del note_paths["folders"][folder]
    logging.debug("[DEBUG] Suppression des dossiers avec path vide terminée.")

    logging.info("[INFO] Fin de la correction de `note_paths.json`")
    return note_paths  # Retourne le dictionnaire nettoyé
