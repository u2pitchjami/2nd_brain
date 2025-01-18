import os
from handlers.config import DIRS
from handlers.import_gpt import process_import_gpt
from handlers.import_normal import import_normal
from handlers.import_syntheses import process_import_syntheses
from handlers.get_type import process_get_note_type
from handlers.files import move_file_with_date
from handlers.files import copy_file_with_date
from handlers.headers import check_type_header
from handlers.prompts import PROMPTS
from datetime import datetime

import logging

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
        print(f"Le fichier {filepath} vient de import.")
        # Appeler la fonction spécifique
        note_type = process_get_note_type(filepath, "type")
        dir_type_name = DIRS[note_type]
        destination_dir = globals().get(dir_type_name)
        move_file_with_date(filepath, dir_type_name)
    elif "gpt_import" in base_folder:
        logging.debug(f"[DEBUG] process_single_note gpt_import")
        process_import_gpt(filepath)
        
        #dir_type_name = DIRS["synthèses_import"]
        #destination_dir = globals().get(dir_type_name)
        #copy_file_with_date(filepath, dir_type_name)
    elif "notes/Technique" in base_folder:
        import_normal(filepath, "technical")
        logging.debug(f"[DEBUG] process_single_note traitement technical")
        dir_type_name = DIRS["synthèses_import"]
        destination_dir = globals().get(dir_type_name)
        copy_file_with_date(filepath, dir_type_name)
    elif "notes/News" in base_folder:
        import_normal(filepath, "news")
        logging.debug(f"[DEBUG] process_single_note traitement news")
        dir_type_name = DIRS["synthèses_import"]
        destination_dir = globals().get(dir_type_name)
        copy_file_with_date(filepath, dir_type_name)
    elif "notes/Idées" in base_folder:
        print(filepath)
        import_normal(filepath, "idea")
        logging.debug(f"[DEBUG] process_single_note traitement idea")
        dir_type_name = DIRS["synthèses_import"]
        destination_dir = globals().get(dir_type_name)
        copy_file_with_date(filepath, dir_type_name)
    elif "notes/Todo" in base_folder:
        import_normal(filepath, "todo")
        logging.debug(f"[DEBUG] process_single_note traitement todo")
        dir_type_name = DIRS["synthèses_import"]
        destination_dir = globals().get(dir_type_name)
        copy_file_with_date(filepath, dir_type_name)
    elif "notes/Tutorial" in base_folder:
        import_normal(filepath, "tutorial")
        logging.debug(f"[DEBUG] process_single_note traitement tutorial")
        dir_type_name = DIRS["synthèses_import"]
        destination_dir = globals().get(dir_type_name)
        copy_file_with_date(filepath, dir_type_name)
    elif "synthèses_import" in base_folder:
        print(f"Le fichier {filepath} vient de 'synthèses_import'.")
        note_type = check_type_header(filepath)
        process_import_syntheses(filepath, note_type)
        dir_type_name = DIRS["synthèses_processed"]
        destination_dir = globals().get(dir_type_name)
        move_file_with_date(filepath, dir_type_name)
        return
    elif "synthèses_processed" in base_folder:
        return
    elif "gpt_processed" in base_folder:
        return
    elif "unknown" in base_folder:
        return
    else:
        note_type = check_type_header(filepath)
        if note_type:
            return
        else:
            dir_type_name = DIRS["imports"]
            destination_dir = globals().get(dir_type_name)
            move_file_with_date(filepath, dir_type_name)
            logging.debug(f"[DEBUG] process_single_note : déplacement de {filepath}")
            return