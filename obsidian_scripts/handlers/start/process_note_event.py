# handlers/start/process_note_event.py
import logging
import re
import os
from datetime import datetime
from pathlib import Path
from handlers.utils.note_index import load_note_index, update_note_index, remove_note_from_index
from handlers.utils.process_note_paths import load_note_paths, save_note_paths
from handlers.utils.extract_yaml_header import extract_tags, extract_status, extract_note_metadata
from handlers.utils.normalization import normalize_path
from Levenshtein import ratio

logger = logging.getLogger()

RELATIVE_PATH = os.getenv('RELATIVE_PATH')

def get_relative_path(filepath):
    """Retourne le chemin relatif d'un fichier par rapport au vault Obsidian"""
    return str(Path(filepath).relative_to(RELATIVE_PATH))

def process_note_event(event):
    """
    Gère les événements liés aux notes (création, modification, suppression).
    Met à jour note_paths.json et l'index des notes avec vérification des doublons.
    """
    logging.debug(f"[DEBUG] process_note_event() a reçu : {event}")
    note_paths = load_note_paths()
    filepath = normalize_path(event["path"])  # 🔥 On normalise le chemin ici
    relative_filepath = str(Path(filepath).relative_to(os.getenv('RELATIVE_PATH')))
    logging.debug(f"[DEBUG] process_note_event() relative_filepath : {relative_filepath}")
    relative_path = get_relative_path(filepath)
    logging.debug(f"[DEBUG] process_note_event() relative_path : {relative_path}")
    logging.debug(f"[DEBUG] Type de filepath avant .stem: {type(filepath)} - Valeur: {filepath}")
    note_title = Path(filepath).stem.replace("_", " ")
    
    # Ignorer les fichiers "Untitled" ou vides
    if note_title.lower() == "untitled" or not note_title.strip():
        logging.info(f"[INFO] Ignoré : fichier temporaire ou sans titre ({filepath})")
        return

    if event['action'] == 'created':
        try:
            logging.debug(f"[DEBUG] Titre de la note extrait : {note_title}")
            if not note_title:
                logging.error(f"[ERREUR] Titre introuvable pour le fichier : {filepath}")
                return
            
            # Vérification des doublons avant ajout
            if check_duplicate(note_title, filepath):
                logging.warning(f"[DOUBLON] Note similaire déjà existante : {note_title}")
                return  # On arrête le traitement si doublon
            logging.debug(f"[DEBUG] sortie check_duplicate")
            
            # Extraction des métadonnées depuis l'entête YAML
            
            title = note_title
            
            new_metadata = {}
                            
            if "Archives" in relative_path:
                new_metadata = extract_note_metadata(filepath)
            
            note_paths['notes'][relative_path] = {
                "title": new_metadata.get("title", title or "Titre inconnu"),  # ✅ Fallback propre
                "category": new_metadata.get("category", None),  # ✅ Optionnel, donc `None`
                "subcategory": new_metadata.get("subcategory", None),  # ✅ Optionnel aussi
                "tags": new_metadata.get("tags", []),  # ✅ Toujours une liste, car c'est une collection
                "status": new_metadata.get("status", "Draft"),  # ✅ Fallback propre
                "created_at": new_metadata.get("created_at", get_file_creation_date(filepath)),  # ✅ Date par défaut
                "modified_at": new_metadata.get("modified_at", get_file_modification_date(filepath))  # ✅ Date par défaut  # ✅ Date de modification mise à jour
            }
            
            logging.debug(f"[DEBUG] Métadonnées extraites")
            # Mettre à jour l'index des notes
            update_note_index(note_title, relative_path)
            logging.info(f"[INFO] Note ajoutée : {relative_path}")

            save_note_paths(note_paths)

        except Exception as e:
            logging.error(f"[ERREUR] Erreur lors du traitement de la note : {e}")
    
    elif event["action"] == "moved":
        logging.debug(f"[DEBUG] process_note_event() a reçu un mouvement pour {event['path']}")
        src_rel_path = str(Path(event["src_path"]).relative_to(os.getenv('RELATIVE_PATH')))
        dest_rel_path = str(Path(event["path"]).relative_to(os.getenv('RELATIVE_PATH')))

        src_path = src_rel_path if src_rel_path.startswith("notes/") else "notes/" + src_rel_path
        dest_path = dest_rel_path if dest_rel_path.startswith("notes/") else "notes/" + dest_rel_path

        if not src_path or not dest_path:
            logging.error(f"[ERREUR] `moved` reçu sans `src_path` ou `path` : {event}")
            return  

        # 🔥 Vérifier si src_path existe avec une clé normalisée
        normalized_keys = {}

        for k in note_paths["notes"].keys():
            if k.startswith("notes/"):
                normalized_keys[k] = k  # 🔹 Déjà relatif, on garde tel quel
            else:
                try:
                    normalized_keys[str(Path(k).relative_to(os.getenv('RELATIVE_PATH')))] = k
                except ValueError:
                    logging.warning(f"[WARNING] Impossible de relativiser {k} avec {os.getenv('RELATIVE_PATH')}, clé conservée telle quelle.")
                    normalized_keys[k] = k  # 🔥 Évite le crash en gardant l'original


        logging.debug(f"[DEBUG] normalized_keys : {normalized_keys}")
        logging.debug(f"[DEBUG] src_path : {src_path}")

        if src_path in normalized_keys:
            original_key = normalized_keys[src_path]  # 🔹 Retrouver la clé correcte

            logging.debug(f"[DEBUG] Mise à jour du chemin : {original_key} → {dest_path}")

            # 🔹 Mise à jour du chemin uniquement
            note_paths["notes"][dest_path] = note_paths["notes"].pop(original_key)
            note_paths["notes"][dest_path]["path"] = dest_path

            save_note_paths(note_paths)
            logging.info(f"[INFO] Déplacement mis à jour pour {dest_path}")


    elif event["action"] == "modified":
        logging.debug(f"[DEBUG] process_note_event() a reçu une modification pour {event['path']}")

        filepath = Path(event["path"])  # 🔹 S'assurer que c'est bien un objet Path
        rel_path = str(filepath.relative_to(os.getenv('RELATIVE_PATH')))
        relative_filepath = rel_path

        # 🔥 Vérifier que la note existe bien dans `note_paths.json`
        if relative_filepath not in note_paths["notes"]:
            logging.error(f"[ERREUR] La note {relative_filepath} n'existe pas dans note_paths.json !")
            return

        # 🔥 Vérifier si le fichier existe encore
        if not filepath.exists():
            logging.warning(f"[WARNING] Le fichier {filepath} n'existe plus physiquement, mise à jour reportée.")
            return  # ⚠️ On ne fait rien, on attend `moved`

        # 🔥 Extraire toutes les métadonnées depuis l'entête YAML
        # 🔹 Récupérer les anciennes métadonnées AVANT de les écraser
        old_metadata = note_paths["notes"].get(relative_filepath, {})

        new_metadata = extract_note_metadata(filepath, old_metadata) 

        # ✅ Mettre à jour `note_paths.json` avec les nouvelles valeurs
        note_paths["notes"][relative_filepath] = {
            "title": new_metadata["title"],  # ✅ Titre mis à jour
            "category": new_metadata["category"],  # ✅ Catégorie mise à jour
            "subcategory": new_metadata["subcategory"],  # ✅ Sous-catégorie mise à jour
            "tags": new_metadata["tags"],  # ✅ Tags extraits de l'entête
            "status": new_metadata["status"],  # ✅ Status mis à jour
            "created_at": new_metadata["created_at"],  # ✅ Date de création depuis l'entête
            "modified_at": new_metadata["modified_at"]  # ✅ Date de modification mise à jour
        }

        # 🔥 Sauvegarde après mise à jour
        save_note_paths(note_paths)
        logging.info(f"[INFO] Métadonnées mises à jour pour {relative_filepath}")
    
    elif event['action'] == 'deleted':
        if relative_path in note_paths['notes']:
            del note_paths['notes'][relative_path]
            remove_note_from_index(note_title)
            logging.info(f"[INFO] Note supprimée de note_paths.json : {relative_path}")
            save_note_paths(note_paths)

def check_duplicate(note_title, filepath):
    """
    Vérifie si un titre de note est un doublon.
    Seule la comparaison est limitée aux notes situées dans des dossiers `storage`.
    Ignorer les fichiers placés dans `ZMake_Header/`.
    """
    logging.debug("check_duplicate")

    # 🔍 Charger `note_paths.json`
    note_paths = load_note_paths()
    folders = note_paths.get("folders", {})

    # 🔍 Convertir `parent_folder` en chemin relatif
    base_path = os.getenv('BASE_PATH')
    parent_folder = os.path.relpath(Path(filepath).parent, base_path)
    parent_folder = f"notes/{parent_folder}"  # Ajout du préfixe "notes/"

    logging.debug("[DEBUG] Parent folder (relatif) : %s", parent_folder)

    # 🚨 Empêcher la détection des doublons si le fichier est dans `ZMake_Header/`
    if "Z_technical/ZMake_Header" in parent_folder or "/Archives/" in parent_folder:
        logging.debug("[INFO] Ignoré: %s car dans ZMake_Header ou Archives", filepath)
        return False  

    # 🔍 Vérification des doublons uniquement avec `storage`
    storage_notes = {
        title: path
        for title, path in load_note_index().items()
        if folders.get(os.path.dirname(path), {}).get("folder_type") == "storage"
        
    }

    logging.debug(f"[DEBUG] load_note_index: {load_note_index()}")
 
    for title, path in load_note_index().items():
        folder = os.path.dirname(path)
        logging.debug(f"[DEBUG] Vérification dossier: {folder}, Existant: {folder in folders}")

    if folders.get(folder, {}).get("folder_type") == "storage":
        storage_notes[title] = path  # Ajout manuel dans un dictionnaire classique

        

    logging.debug("[DEBUG] Nombre de notes en `storage` pour comparaison : %d", len(storage_notes))

    for existing_title, existing_path in storage_notes.items():
        similarity = ratio(clean_title(note_title), clean_title(existing_title))

        if similarity >= 0.9:
            logging.warning("[DOUBLON] Note similaire détectée dans `storage`: %s (similarité : %.2f)", existing_title, similarity)
            move_duplicate_to_folder(filepath)
            return True  

    return False  



def extract_category_from_path(path):
    parts = Path(path).parts
    if len(parts) > 1:
        return parts[1].lower()  # On passe en minuscules pour plus de cohérence
    logging.warning(f"[WARN] Aucune catégorie détectée dans le chemin : {path}")
    return "uncategorized"  # Catégorie par défaut si rien trouvé

def extract_subcategory_from_path(path):
    parts = Path(path).parts
    return parts[2] if len(parts) > 2 else None

def get_file_creation_date(path):
    timestamp = Path(path).stat().st_ctime
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')

def get_file_modification_date(path):
    timestamp = Path(path).stat().st_mtime
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')

def clean_title(title):
    # Supprimer les chiffres de date et les underscores pour une meilleure comparaison
    return re.sub(r'^\d{6}_?', '', title.replace('_', ' ')).lower()

def move_duplicate_to_folder(filepath):
    """
    Déplace la note en doublon dans le dossier Z_technical/duplicates.
    """
    logging.debug(f"[DEBUG] move_duplicate_to_folder {filepath}")
    duplicates_folder = Path(os.getenv('BASE_PATH')) / "Z_technical" / "duplicates"
    logging.debug(f"[DEBUG] move_duplicate_to_folder {duplicates_folder}")
    duplicates_folder.mkdir(parents=True, exist_ok=True)

    note_path = Path(filepath)
    new_path = duplicates_folder / note_path.name

    try:
        note_path.rename(new_path)
        logging.info(f"[DOUBLON] Note déplacée dans le dossier des doublons : {new_path}")
    except Exception as e:
        logging.error(f"[ERREUR] Impossible de déplacer le doublon : {e}")

