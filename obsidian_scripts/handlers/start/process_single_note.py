import os
from handlers.process_imports.import_gpt import process_import_gpt, process_clean_gpt, process_class_gpt
from handlers.process_imports.import_normal import import_normal
from handlers.process_imports.import_syntheses import process_import_syntheses
from handlers.process.get_type import process_get_note_type, categ_extract
from handlers.utils.files import rename_file, is_in_excluded_folder
from handlers.standalone.standalone import make_synthese_standalone, make_header_standalone
from handlers.standalone.check_categ import process_sync_entete_with_path
import logging
from pathlib import Path
import fnmatch
logger = logging.getLogger()



def process_single_note(filepath, dest_path=None):
    logging.debug(f"[DEBUG] démarrage du process_single_note pour : {filepath}")
    if not filepath.endswith(".md"):
        return
    # Obtenir le dossier contenant le fichier
    base_folder = os.path.dirname(filepath)
    
    def process_import(filepath, base_folder):
        """ Fonction interne pour éviter la duplication de code """
        logging.info(f"[INFO] Import détecté : {filepath}")
        try:
            new_path = process_get_note_type(filepath)
            logging.debug(f"[DEBUG] process_single_note fin get_note_type new_path : {new_path}")
            filepath = new_path
            base_folder = os.path.dirname(new_path)
            logging.debug(f"[DEBUG] process_single_note base_folder : {base_folder}")
            new_path = rename_file(filepath)
            logging.debug(f"[DEBUG] process_single_note fin rename_file : {new_path}")
            filepath = new_path
            if "gpt_import" in base_folder:
                logging.info(f"[INFO] Conversation GPT détectée, déplacement vers : {base_folder}")
                return
            category, subcategory = categ_extract(base_folder)
            import_normal(filepath, category, subcategory)
            logging.debug(f"[DEBUG] process_single_note import normal terminé {category}/{subcategory}")
            process_import_syntheses(filepath, category, subcategory)
            logging.info(f"[INFO] Import terminé pour : {filepath}")
        except Exception as e:
            logging.error(f"[ERREUR] Problème lors de l'import : {e}")
     
    
    
    
    
    
    
    # 1. Vérifier si c'est un déplacement
    if dest_path is not None:
        logging.debug(f"[DEBUG] démarrage du process_single_note pour : Déplacement {dest_path}")
        if not os.path.exists(dest_path):
            logging.warning(f"[WARNING] Le fichier n'existe pas ou plus : {dest_path}")
            return
        dest_folder = os.path.dirname(dest_path)

        # 1.1 Déplacement valide entre dossiers catégorisés (hors exclus)
        if not (is_in_excluded_folder(filepath) or is_in_excluded_folder(dest_path)):
            logging.info(f"[INFO] Déplacement valide détecté : {filepath} -> {dest_path}")
            process_sync_entete_with_path(dest_path)
            return  # Sortir après le traitement du déplacement
        
        elif "imports" in base_folder:
            process_import(filepath, base_folder)
        
        elif "gpt_output" in base_folder:
            logging.info(f"[INFO] Import issu d'une conversation GPT : {filepath}")
            try:
                process_clean_gpt(filepath)
                new_path = process_get_note_type(filepath)
                base_folder = os.path.dirname(new_path)
                filepath = new_path
                new_path = rename_file(filepath)
                logging.info(f"[INFO] Note renommée : {filepath} --> {new_path}")
                filepath = new_path
                category, subcategory = categ_extract(base_folder)
                process_class_gpt(filepath, category, subcategory)
                logging.info(f"[INFO] Import terminé pour : {filepath}")
                return
            except Exception as e:
                logging.error(f"[ERREUR] Anomalie l'import gpt : {e}")
                return

        # 1.2 Autres déplacements (exemple : ZMake)
        elif "ZMake_Synthese" in dest_folder:
            logging.info(f"[INFO] Déplacement manuel vers ZMake_Synthese : {filepath} -> {dest_path}")
            make_synthese_standalone(dest_path)
            return

        elif "ZMake_Header" in dest_folder:
            logging.info(f"[INFO] Déplacement manuel vers ZMake_Header : {filepath} -> {dest_path}")
            make_header_standalone(dest_path)
            return

        # Autres cas : déplacement ignoré
        else:
            logging.info(f"[INFO] Déplacement ignoré : {filepath} -> {dest_path}")
            return

    # 2. Sinon : Gérer les créations ou modifications
    else:
        logging.debug(f"[DEBUG] démarrage du process_single_note pour : création - modif")
        if not os.path.exists(filepath):
            logging.warning(f"[WARNING] Le fichier n'existe pas ou plus : {filepath}")
            return
        if "imports" in base_folder:
            process_import(filepath, base_folder)

        elif "gpt_import" in base_folder:
            logging.info(f"[INFO] Split de la conversation GPT : {filepath}")
            try:
                logging.debug(f"[DEBUG] process_single_note : envoi vers gpt_import")
                process_import_gpt(filepath)
                return
            except Exception as e:
                logging.error(f"[ERREUR] Anomalie l'import gpt : {e}")
                return

        

        else:
            # Traitement pour les autres cas
            logging.debug(f"[DEBUG] Aucune correspondance pour : {filepath}")
            return