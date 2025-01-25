from handlers.config import NOTE_PATHS
from handlers.get_type import extract_category_and_subcategory
from handlers.get_type import get_path_from_classification
from handlers.import_syntheses import process_import_syntheses
import logging
from pathlib import Path
import shutil
import os

logger = logging.getLogger(__name__)

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