from handlers.large_note import process_large_note
from handlers.divers import read_note_content
from handlers.divers import clean_content
from handlers.files import copy_file_with_date
from handlers.files import move_file_with_date
from datetime import datetime
import logging

def import_normal(filepath):
    logging.debug(f"[DEBUG] démarrage du process_import_gpt pour : {filepath}")
    
    content = read_note_content(filepath)
    lines = content.splitlines()
    try:    
        cleaned_content = clean_content(content, filepath)

        # Définir le seuil de mots pour déclencher l'analyse
        nombre_mots_actuels = count_words(cleaned.content)
        max_words_for_large_note = 1000  # Définir la limite de mots pour une "grande" note
        content = cleaned_content 
        # Lire les métadonnées existantes
        logging.debug(f"[DEBUG] process_single_note lecture des metadonnees {filepath}")
           
        
        # Conditions d'analyse
                
        # Détection de modification significative
        if nombre_mots_actuels >= max_words_for_large_note:
            print("[INFO] Note de + de",max_words_for_large_note,"mots")
            logging.debug(f"[DEBUG] import_syntheses : note de grande taille {filepath}")
            
            logging.debug(f"[DEBUG] process_single_note : envoie process_large {filepath}")
            process_large_note(content, filepath, "synthese")
            logging.debug(f"[DEBUG] process_single_note :retour du process_large {filepath}")
            
            logging.debug(f"[DEBUG] process_single_note : import normal envoi vers process & update {filepath}")
            process_and_update_file(filepath)
            logging.debug(f"[DEBUG] process_single_note : import normal envoi vers make_properties {filepath}")
            make_properties(content, filepath)

        else:
            
            logging.debug(f"[DEBUG] process_single_note : note < {max_words_for_large_note}")
            content = cleaned_content
            # Reformulation normale et vérification de la taille
            logging.debug(f"[DEBUG] process_single_note : envoie vers simplified note de {filepath}")
            simplified_note = simplify_note_with_ai(content)
            content = simplified_note
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(content)
                logging.debug(f"[DEBUG] creation de {filepath}")
            logging.debug(f"[DEBUG] process_single_note : envoie vers process_and_update_file de {filepath}")
            process_and_update_file(filepath)
            logging.debug(f"[DEBUG] process_single_note : envoie vers make_properties de {filepath}")
            make_properties(content, filepath)
      
    except Exception as e:
        print(f"[ERREUR] Impossible de traiter {filepath} : {e}")

def process_import_syntheses(filepath):
    logging.debug(f"[DEBUG] démarrage du process_import_gpt pour : {filepath}")
    
    content = read_note_content(filepath)
    
    #creation d'une copie de sauvegarde :
    copy_file_with_date(filepath, "/mnt/user/Documents/Obsidian/notes/.sav")
    logging.debug(f"[DEBUG] process_import_gpt : sauvegarde de {filepath}")
        
    logging.debug(f"[DEBUG] process_import_gpt : envoie vers clean content {filepath}")
    content = clean_content(content, filepath)
    
    logging.debug(f"[DEBUG] process_single_note : envoie process_large")
    process_large_note(content, filepath)
    logging.debug(f"[DEBUG] process_single_note :retour du process_large")
    
    #creation d'une copie de sauvegarde :
    move_file_with_date(filepath, "/mnt/user/Documents/Obsidian/notes/gpt_processed")
    logging.debug(f"[DEBUG] process_import_gpt : déplacement de {filepath}")
    
    