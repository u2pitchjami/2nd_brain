from handlers.large_note import process_large_note
from handlers.divers import read_note_content
from handlers.divers import clean_content
from handlers.divers import count_words
from handlers.headers import make_properties
from handlers.split_note import should_split_note
from handlers.keywords import process_and_update_file
from handlers.ollama import simplify_note_with_ai
import logging

def import_normal(filepath):
    logging.debug(f"[DEBUG] démarrage du process_import_gpt pour : {filepath}")
    
    content = read_note_content(filepath)
    lines = content.splitlines()
    try:    
        cleaned_content = clean_content(content, filepath)

        # Définir le seuil de mots pour déclencher l'analyse
        nombre_mots_actuels = count_words(content)
        seuil_mots_initial = 100
        seuil_modif = 100
        ancienne_valeur = 0
        
        # Lire les métadonnées existantes
        logging.debug(f"[DEBUG] process_single_note lecture des metadonnees {filepath}")
           
        for line in lines:
            if line.startswith("word_count:"):
                try:
                    ancienne_valeur = int(line.split(":")[1].strip())
                    logging.debug(f"[DEBUG] process_single_note ligne word_count trouvée {filepath}")
                except ValueError:
                    ancienne_valeur = 0  # Si la valeur est absente ou invalide
                                    
            if line.startswith("created:"):
                logging.debug(f"[DEBUG] process_single_note ligne created trouvée {filepath}")
                date_creation = line.split(":")[1].strip()
                    
        print(f"[INFO] Mots avant modif : {ancienne_valeur}, Mots actuels : {nombre_mots_actuels}")
        logging.debug(f"[DEBUG] process_single_note Mots avant modif : {ancienne_valeur}, Mots actuels : {nombre_mots_actuels}-->{filepath}")
        # Conditions d'analyse
        if nombre_mots_actuels < seuil_mots_initial:
            print("[INFO] Note trop courte. Aucun traitement.")
            logging.debug(f"[DEBUG] process_single_note : note courte")
            return
        
        # Détection de modification significative
        if nombre_mots_actuels - ancienne_valeur >= seuil_modif or ancienne_valeur == 0:
            print("[INFO] Modification significative détectée. Reformulation du texte.")
            logging.debug(f"[DEBUG] process_single_note : modif significative {filepath}")
            # Nettoyer le contenu
            logging.debug(f"[DEBUG] process_single_note : envoie pour vers clean_content {filepath}")
            cleaned_content = clean_content(content, filepath)
            # Vérifier si la note est volumineuse
            word_count = len(cleaned_content.split())
            max_words_for_large_note = 1000  # Définir la limite de mots pour une "grande" note
            logging.debug(f"[DEBUG] process_single_note nombre mots : {word_count} --> {filepath}")
            if word_count > max_words_for_large_note:
                print(f"[INFO] La note est volumineuse ({word_count} mots). Utilisation de 'process_large_note'.")
                logging.debug(f"[DEBUG] process_single_note : note > {max_words_for_large_note}")
                content = cleaned_content
                logging.debug(f"[DEBUG] process_single_note : envoie process_large {filepath}")
                process_large_note(content, filepath)
                logging.debug(f"[DEBUG] process_single_note :retour du process_large {filepath}")
                #if not should_split_note(filepath, content):
                #    print(f"[INFO] La note est suffisamment courte, pas de split nécessaire : {filepath}")
                #    logging.debug(f"[DEBUG] remplacement de la note par la simplification")
                #    make_properties(content, filepath)
                # Étape 3 : Splitter la note si nécessaire
                # Splitter la note directement avec les titres existants (## ou ###)
                #logging.debug(f"[DEBUG] Début du split basé sur les titres")
                
                # Découpe les sections avec les titres Markdown
                #sections = split_by_headings(content)
                #logging.debug(f"[DEBUG] Sections après split_by_headings : {sections}")

                # Filtre les sections trop courtes
                #sections = filter_short_sections(sections, min_word_count=100)
                #logging.debug(f"[DEBUG] Sections après filtre : {sections}")
                #create_split_notes(filepath, sections)
                logging.debug(f"[DEBUG] process_single_note : import normal envoi vers process & update {filepath}")
                process_and_update_file(filepath)
                logging.debug(f"[DEBUG] process_single_note : import normal envoi vers make_properties {filepath}")
                make_properties(content, filepath)

            else:
                # Nettoyer le contenu
                #cleaned_content = clean_content(content)
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
        else:
            print("[INFO] Modification non significative. Pas de mise à jour.")
            logging.debug(f"[DEBUG] process_single_note pas suffisament de modif")   
    except Exception as e:
        print(f"[ERREUR] Impossible de traiter {filepath} : {e}")