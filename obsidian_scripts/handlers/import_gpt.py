from handlers.large_note import process_large_note
from handlers.divers import read_note_content
from handlers.divers import clean_content
from handlers.split_note import split_note_by_subject
from handlers.files import copy_file_with_date
from handlers.files import move_file_with_date
from datetime import datetime
import logging

def process_import_gpt(filepath):
    logging.debug(f"[DEBUG] démarrage du process_import_gpt pour : {filepath}")
    
    content = read_note_content(filepath)
    
    #creation d'une copie de sauvegarde :
    copy_file_with_date(filepath, "/mnt/user/Documents/Obsidian/notes/.sav")
    logging.debug(f"[DEBUG] process_import_gpt : sauvegarde de {filepath}")
        
    logging.debug(f"[DEBUG] process_import_gpt : envoie vers clean content {filepath}")
    content = clean_content(content, filepath)
    
    logging.debug(f"[DEBUG] process_import_gpt : envoie split_note_by_subject")
    final_content = split_note_by_subject(content)
    logging.debug(f"[DEBUG] process_import_gpt :retour du split_note_by_subject")
    
    with open(filepath, 'w', encoding='utf-8') as file:
            file.write(final_content)
    
    #mouvement :
    move_file_with_date(filepath, "/mnt/user/Documents/Obsidian/notes/gpt_processed")
    logging.debug(f"[DEBUG] process_import_gpt : déplacement de {filepath}")
    
    