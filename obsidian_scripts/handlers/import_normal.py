from handlers.large_note import process_large_note
from handlers.files import read_note_content
from handlers.files import clean_content
from handlers.files import count_words
from handlers.headers import make_properties
from handlers.keywords import process_and_update_file
from handlers.files import copy_file_with_date
import os
import logging

logger = logging.getLogger(__name__)

def import_normal(filepath, category, subcategory):
    logging.debug(f"[DEBUG] démarrage du process_import_normal pour : {filepath}")
    try:
        sav_dir = os.getenv('SAV_DIR')
        copy_file_with_date(filepath, sav_dir)
        content = read_note_content(filepath)
        lines = content.splitlines()
        
        cleaned_content = clean_content(content, filepath)

        # Définir le seuil de mots pour déclencher l'analyse
        nombre_mots_actuels = count_words(content)
        seuil_mots_initial = 100
        seuil_modif = 100
        ancienne_valeur = 0
        
        # Lire les métadonnées existantes
        logging.debug(f"[DEBUG] import_normal lecture des metadonnees {filepath}")
           
        for line in lines:
            if line.startswith("word_count:"):
                try:
                    ancienne_valeur = int(line.split(":")[1].strip())
                    logging.debug(f"[DEBUG] import_normal ligne word_count trouvée {filepath}")
                except ValueError:
                    ancienne_valeur = 0  # Si la valeur est absente ou invalide
                                    
            if line.startswith("created:"):
                logging.debug(f"[DEBUG] import_normal ligne created trouvée {filepath}")
                date_creation = line.split(":")[1].strip()
                    
        logging.info(f"[INFO] Mots avant modif : {ancienne_valeur}, Mots actuels : {nombre_mots_actuels}")
        logging.debug(f"[DEBUG] import_normal Mots avant modif : {ancienne_valeur}, Mots actuels : {nombre_mots_actuels}-->{filepath}")
        # Conditions d'analyse
        if nombre_mots_actuels < seuil_mots_initial:
            logging.info("[INFO] Note trop courte. Aucun traitement.")
            logging.debug(f"[DEBUG] import_normal : note courte")
            return
        
        # Détection de modification significative
        if nombre_mots_actuels - ancienne_valeur >= seuil_modif or ancienne_valeur == 0:
            logging.info("[INFO] Modification significative détectée. Reformulation du texte.")
            logging.debug(f"[DEBUG] import_normal : modif significative {filepath}")
            # Nettoyer le contenu
            logging.debug(f"[DEBUG] import_normal : envoie pour vers clean_content {filepath}")
            cleaned_content = clean_content(content, filepath)
            content = cleaned_content
            logging.debug(f"[DEBUG] import_normal : envoie process_large {filepath}")
            process_large_note(content, filepath, "reformulation")
            logging.debug(f"[DEBUG] import_normal :retour du process_large {filepath}")
            logging.debug(f"[DEBUG] import_normal : import normal envoi vers process & update {filepath}")
            process_and_update_file(filepath)
            logging.debug(f"[DEBUG] import_normal : import normal envoi vers make_properties {filepath}")
            make_properties(content, filepath, category, subcategory)
            
            
            return
        else:
            print("[INFO] Modification non significative. Pas de mise à jour.")
            logging.debug(f"[DEBUG] import_normal pas suffisament de modif")   
    except Exception as e:
        print(f"[ERREUR] Impossible de traiter {filepath} : {e}")