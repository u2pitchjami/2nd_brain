from handlers.utils.process_note_paths import get_path_from_classification
from handlers.utils.extract_yaml_header import extract_category_and_subcategory, extract_status
from handlers.utils.files import read_note_content
from handlers.process_imports.import_syntheses import process_import_syntheses
from handlers.process.headers import make_properties
from handlers.process.keywords import process_and_update_file
import logging
from pathlib import Path
import shutil
import os

logger = logging.getLogger()

def make_synthese_standalone(filepath):
        
    # Étape 1 : Lire l'entête pour récupérer catégorie et sous-catégorie
    category, subcategory = extract_category_and_subcategory(filepath)
    logging.debug("[DEBUG] make_synthese_standalone %s %s",category, subcategory)
    if not category or not subcategory:
        logging.error(f"[ERREUR] Impossible d'extraire les informations du fichier : {filepath}")
        raise
    
    # Étape 2 : Trouver le chemin cible
    target_path = get_path_from_classification(category, subcategory)
    logging.debug("[DEBUG] make_synthese_standalone target_path %s",target_path)
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
            logging.warning(f"[ATTENTION] Impossible de supprimer {original_file} (peut-être déjà supprimé ?) : {e}")
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
    logging.debug("[DEBUG] make_header_standalone %s %s",category, subcategory)
    if not category or not subcategory:
        logging.error(f"[ERREUR] Impossible d'extraire les informations du fichier : {filepath}")
        raise
    
    # Étape 2 : Trouver le chemin cible
    target_path = get_path_from_classification(category, subcategory)
    logging.debug("[DEBUG] make_sheader_standalone target_path %s",target_path)
    if not target_path:
        logging.error(f"[ERREUR] Aucun chemin trouvé pour category={category}, subcategory={subcategory}")
        raise
    
    # Étape 3 : Lire l'entête pour récupérer le statut
    status = extract_status(filepath)
    logging.debug("[DEBUG] make_header_standalone status %s",status)
    if not status:
        logging.error(f"[ERREUR] Impossible d'extraire le statut du fichier : {filepath}")
        raise
    
    # Étape 4 : Construire le chemin complet de l'ancienne synthèse
    filename = os.path.basename(filepath)
    logging.debug(f"[DEBUG] filename {filename}")
    if status == "archive":
        original_file = Path(target_path) / status / filename
    else:
        original_file = Path(target_path) / filename

    target_path = original_file
    logging.debug(f"[DEBUG] target_path {filename}")
    # 🔍 Vérifications avant le déplacement
    logging.debug(f"[DEBUG] Vérification du déplacement de {filepath} vers {target_path}")

    if not Path(filepath).exists():
        logging.error(f"[ERREUR] Le fichier source {filepath} n'existe plus, annulation du déplacement.")
        return

    if not Path(target_path).parent.exists():
        logging.warning(f"[WARNING] Le dossier de destination {Path(target_path).parent} n'existe pas, création en cours.")
        Path(target_path).parent.mkdir(parents=True, exist_ok=True)

    # Déplacement du fichier
    try:
        shutil.move(filepath, target_path)
        logging.info(f"[INFO] Fichier déplacé avec succès vers {target_path}")
    except Exception as e:
        logging.error(f"[ERREUR] Impossible de déplacer {filepath} vers {target_path} : {e}")
        return

    filepath = original_file  # Mise à jour du chemin
    # Étape 5 : Relancer la génération de synthèse
    
    try:
        content = read_note_content(filepath)
        if status == "archive":
            logging.debug(f"[DEBUG] envoi vers process & update {filepath}")
            process_and_update_file(filepath)
            logging.info(f"[INFO] Keywords mis à jour")
        logging.debug(f"[DEBUG] vers make_properties {filepath}")
        logging.debug(f"[DEBUG] make_properties() - File: {filepath}, Category: {category}, Subcategory: {subcategory}, Status: {status}")
        make_properties(content, filepath, category, subcategory, status)
        logging.info(f"[INFO] Entête régénérée")    
        
        
        
    except Exception as e:
        logging.error(f"[ERREUR] Échec lors de la régénération de l'entête' : {e}")
        raise   
    
