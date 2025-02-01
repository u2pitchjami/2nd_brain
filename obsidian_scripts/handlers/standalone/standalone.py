from handlers.process.get_type import load_note_paths, extract_category_and_subcategory, extract_status, get_path_from_classification
from handlers.utils.files import read_note_content
from handlers.process_imports.import_syntheses import process_import_syntheses
from handlers.process.headers import make_properties
from handlers.process.keywords import process_and_update_file
import logging
from pathlib import Path
import shutil
import os

logger = logging.getLogger()

note_paths_file = os.getenv('NOTE_PATHS_FILE')    
NOTE_PATHS = load_note_paths(note_paths_file)
note_paths = NOTE_PATHS

def make_synthese_standalone(filepath):
        
    # Étape 1 : Lire l'entête pour récupérer catégorie et sous-catégorie
    category, subcategory = extract_category_and_subcategory(filepath)
    if not category or not subcategory:
        logging.error(f"[ERREUR] Impossible d'extraire les informations du fichier : {filepath}")
        raise
    
    # Étape 2 : Trouver le chemin cible
    target_path = get_path_from_classification(category, subcategory, NOTE_PATHS)
    if not target_path:
        logging.error(f"[ERREUR] Aucun chemin trouvé pour category={category}, subcategory={subcategory}")
        raise
    
    # Étape 3 : Construire le chemin complet de l'ancienne synthèse
    filename = os.path.basename(filepath)
    original_file = target_path / filename
    if original_file.exists():
        try:
            original_file.unlink()  # Supprimer le fichier
            logging.info(f"[INFO] Synthèse originale supprimée : {original_file}")
        except Exception as e:
            logging.error(f"[ERREUR] Échec de la suppression de {original_file} : {e}")
            raise
    else:
        logging.warning(f"[ATTENTION] Aucun fichier à supprimer trouvé pour : {original_file}")
    
    # Déplacer le fichier
    shutil.move(filepath, target_path)
    filepath = original_file
    # Étape 4 : Relancer la génération de synthèse
    try:
        process_import_syntheses(filepath, category, subcategory)
        logging.info(f"[INFO] Synthèse régénérée pour category={category}, subcategory={subcategory}")
    except Exception as e:
        logging.error(f"[ERREUR] Échec lors de la régénération de la synthèse : {e}")
        raise   
    
    
def make_header_standalone(filepath):
        
    # Étape 1 : Lire l'entête pour récupérer catégorie et sous-catégorie
    category, subcategory = extract_category_and_subcategory(filepath)
    if not category or not subcategory:
        logging.error(f"[ERREUR] Impossible d'extraire les informations du fichier : {filepath}")
        raise
    
    # Étape 2 : Trouver le chemin cible
    target_path = get_path_from_classification(category, subcategory, NOTE_PATHS)
    if not target_path:
        logging.error(f"[ERREUR] Aucun chemin trouvé pour category={category}, subcategory={subcategory}")
        raise
    
    # Étape 3 : Lire l'entête pour récupérer le statut
    status = extract_status(filepath)
    if not status:
        logging.error(f"[ERREUR] Impossible d'extraire le statut du fichier : {filepath}")
        raise
    
    # Étape 4 : Construire le chemin complet de l'ancienne synthèse
    filename = os.path.basename(filepath)
    if status == "archive":
        original_file = target_path / status / filename
    else:
        original_file = target_path / filename
        
    target_path = original_file   
       
    # Déplacer le fichier
    shutil.move(filepath, target_path)
    filepath = original_file
    # Étape 5 : Relancer la génération de synthèse
    
    try:
        content = read_note_content(filepath)
        if status == "archive":
            logging.debug(f"[DEBUG] envoi vers process & update {filepath}")
            process_and_update_file(filepath)
            logging.info(f"[INFO] Keywords mis à jour")
        logging.debug(f"[DEBUG] vers make_properties {filepath}")
        make_properties(content, filepath, category, subcategory, status)
        logging.info(f"[INFO] Entête régénérée")    
        
        
        
    except Exception as e:
        logging.error(f"[ERREUR] Échec lors de la régénération de l'entête' : {e}")
        raise   
    
