import os
from handlers.import_gpt import process_import_gpt
from handlers.import_gpt import process_clean_gpt
from handlers.import_gpt import process_class_gpt
from handlers.import_normal import import_normal
from handlers.import_syntheses import process_import_syntheses
from handlers.get_type import process_get_note_type
from handlers.get_type import categ_extract
from handlers.files import rename_file
from handlers.standalone import make_synthese_standalone
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def process_single_note(filepath):
    logging.debug(f"[DEBUG] démarrage du process_single_note pour : {filepath}")
    
    if not os.path.exists(filepath):
        logging.warning(f"[WARNING] Le fichier n'existe pas ou plus : {filepath}")
        return
    
    if not filepath.endswith(".md"):
        return
    
    # Obtenir le dossier contenant le fichier
    base_folder = os.path.dirname(filepath)
    
    # Vérifie si le fichier vient de 'imports'
    if "imports" in base_folder:
        logging.info(f"[INFO] Import de : {filepath}")
        # Appeler la fonction spécifique
        try:
            new_path = rename_file(filepath)
            filepath = new_path
            new_path = process_get_note_type(filepath)
            filepath = new_path
            base_folder = os.path.dirname(new_path)
            if "gpt_import" in base_folder:
                logging.info(f"[INFO] Conversation GPT détectée, déplacement vers : {base_folder}")
                return
            category, subcategory = categ_extract(base_folder)
            import_normal(filepath, category, subcategory)
            logging.debug(f"[DEBUG] process_single_note import normal terminé {category}/{subcategory}")
            process_import_syntheses(filepath, category, subcategory)
            logging.info(f"[INFO] Import terminé pour : {filepath}")
            return
        except Exception as e:
            logging.error(f"[ERREUR] Anomalie lors du traitement du fichier : {e}")
            return
    elif "gpt_import" in base_folder:
        logging.info(f"[INFO] Split de la conversation GPT : {filepath}")
        try:
                       
            logging.debug(f"[DEBUG] process_single_note : envoi vers gpt_import")
            process_import_gpt(filepath)
            return
        except Exception as e:
            logging.error(f"[ERREUR] Anomalie l'import gpt : {e}")
            return
    
    elif "gpt_output" in base_folder:   
        logging.info(f"[INFO] Import issu d'une conversation GPT : {filepath}")
        try:
            new_path = rename_file(filepath)
            logging.info(f"[INFO] Note renommée : {filepath} --> {new_path}")
            filepath = new_path
            process_clean_gpt(filepath)
            new_path = process_get_note_type(filepath)
            base_folder = os.path.dirname(new_path)
            filepath = new_path
            category, subcategory = categ_extract(base_folder)
            process_class_gpt(filepath, category, subcategory)
            logging.info(f"[INFO] Import terminé pour : {filepath}")
            return
        except Exception as e:
            logging.error(f"[ERREUR] Anomalie l'import gpt : {e}")
            return
    elif "ZMake_Synthese" in base_folder:   
        logging.info(f"[INFO] Génération d'une nouvelle synthèse pour : {filepath}")
        try:
            make_synthese_standalone(filepath)
            return
        except Exception as e:
            logging.error(f"[ERREUR] Anomalie l'import gpt : {e}")
            return
    
    else:
        # Traitement pour les autres cas
        logging.debug(f"[DEBUG] Aucune correspondance pour : {filepath}")
        return