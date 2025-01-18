from handlers.large_note import process_large_note
from handlers.divers import read_note_content
from handlers.divers import clean_content
from handlers.files import copy_file_with_date
from handlers.files import move_file_with_date
from handlers.headers import make_properties
from handlers.keywords import process_and_update_file
from handlers.extract_yaml_header import extract_yaml_header
from datetime import datetime
import logging

def process_import_syntheses(filepath, note_type):
    logging.debug(f"[DEBUG] démarrage du process_import_synthèse pour : {filepath}")
    try:
        content = read_note_content(filepath)
       #with open(filepath, "r", encoding="utf-8") as file:
       #     content = file.readlines()
        logging.debug(f"[DEBUG] Contenu brut : {repr(content[:100])}...")  # Limité pour éviter de surcharger
        logging.debug(f"[DEBUG] Type après lecture : {type(content)}")
        copy_file_with_date(filepath, "/mnt/user/Documents/Obsidian/notes/.sav")
        
        cleaned_content = clean_content(content, filepath)
        content = cleaned_content
        
        logging.debug(f"[DEBUG] process_import_syntheses : pouet {filepath}")
        #header_lines, content_lines = extract_yaml_header(content)
        #content = content_lines
        #logging.debug(f"[DEBUG] pouet {header_lines}")
        process_large_note(content, filepath, "synthese")
        content = read_note_content(filepath)
        process_large_note(content, filepath, "synthese2")        
        logging.debug(f"[DEBUG] process_import_syntheses : import normal envoi vers process & update {filepath}")
        #process_and_update_file(filepath)
        logging.debug(f"[DEBUG] process_import_syntheses : import normal envoi vers make_properties {filepath}")
        make_properties(content, filepath, note_type)
        return
        #mouvement :
        #move_file_with_date(filepath, "/mnt/user/Documents/Obsidian/notes/synthèses_processed")
        #logging.debug(f"[DEBUG] process_import_syntheses : déplacement de {filepath}")
        
      
    except Exception as e:
        print(f"[ERREUR] Impossible de traiter {filepath} : {e}")    