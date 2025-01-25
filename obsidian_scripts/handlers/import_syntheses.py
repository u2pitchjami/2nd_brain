from handlers.prompts import PROMPTS
from handlers.ollama import ollama_generate
from handlers.config import NOTE_PATHS
from handlers.files import read_note_content
from handlers.files import copy_to_archives
from handlers.files import make_relative_link
from handlers.files import clean_content
from handlers.files import copy_file_with_date
from handlers.files import move_file_with_date
from handlers.headers import make_properties
from handlers.keywords import process_and_update_file
from handlers.extract_yaml_header import extract_yaml_header
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def process_import_syntheses(filepath, category, subcategory):
    logging.info(f"[INFO] Génération de la synthèse pour : {filepath}")
    logging.debug(f"[DEBUG] démarrage du process_import_synthèse pour : {category} / {subcategory}")
    try:
        content = read_note_content(filepath)
       #with open(filepath, "r", encoding="utf-8") as file:
       #     content = file.readlines()
        logging.debug(f"[DEBUG] Contenu brut : {repr(content[:100])}...")  # Limité pour éviter de surcharger
        logging.debug(f"[DEBUG] Type après lecture : {type(content)}")
        
        
        logging.debug(f"[DEBUG] process_single_note lancement copy_to_archives")
                
        new_path = copy_to_archives(filepath)
        original_path = new_path
        original_path = make_relative_link(original_path, link_text="Voir la note originale")
        logging.debug(f"[DEBUG] process_single_note : original_path {original_path}")
        
        
        header_lines, content_lines = extract_yaml_header(content)
        content = content_lines
        logging.debug(f"[DEBUG] process_import_synthese : original_path {original_path}")              
        make_syntheses(filepath, content, header_lines, category, subcategory, original_path)        
        #logging.debug(f"[DEBUG] process_import_syntheses : envoi vers process & update {filepath}")
        process_and_update_file(filepath)
        logging.debug(f"[DEBUG] process_import_syntheses : envoi vers make_properties {filepath}")
        
        make_properties(content, filepath, category, subcategory)
        logging.info(f"[INFO] Synthèse terminée pour {filepath}")
        return
        
      
    except Exception as e:
        print(f"[ERREUR] Impossible de traiter {filepath} : {e}")    
        
def make_syntheses(filepath, content, header_lines, category, subcategory, original_path):
    logging.debug(f"[DEBUG] démarrage de make_synthèse pour ")
    try:
        prompt_name = get_prompt_name(category, subcategory, NOTE_PATHS)
        #prompt_name = "synthese2"
        logging.debug(f"[DEBUG] make_syntheses : prompt : {prompt_name}")
        prompt = PROMPTS[prompt_name].format(content=content) 
        logging.debug(f"[DEBUG] make_syntheses : prompt : {prompt}")            
        logging.debug(f"[DEBUG] make_syntheses : envoie vers ollama")    
        response = ollama_generate(prompt)
        logging.debug(f"[DEBUG] make_syntheses : type de response : {type(response)}")
        logging.debug(f"[DEBUG] make_syntheses : contenu de response : {response[:50]}")
        
        prompt_name = "synthese2"
        logging.debug(f"[DEBUG] make_syntheses : prompt : {prompt_name}")
        prompt = PROMPTS[prompt_name].format(content=response) 
        logging.debug(f"[DEBUG] make_syntheses : prompt : {prompt}")            
        logging.debug(f"[DEBUG] make_syntheses : envoie vers ollama")    
        response = ollama_generate(prompt)
        logging.debug(f"[DEBUG] make_syntheses : type de response : {type(response)}")
        logging.debug(f"[DEBUG] make_syntheses : contenu de response : {response[:50]}")
        
        # Étape 3 : Fusionner les blocs reformulés
        header_content = "\n".join(header_lines).strip()
        logging.debug(f"[DEBUG] make_syntheses header_content : {header_content[:50]}")
        # Construire le contenu principal
        if isinstance(response, str):
            body_content = response.strip()
        elif isinstance(response, list):
            body_content = "\n\n".join(block.strip() for block in response if isinstance(block, str)).strip()
        else:
            raise ValueError("Response de ollama_generate n'est ni une chaîne ni une liste valide")
        logging.debug(f"[DEBUG] make_syntheses body_content : {body_content[:50]}")
        # Construire le lien vers la note originale
        logging.debug(f"[DEBUG] process_import_synthese : original_path {original_path}") 
        original_link = f"[Voir la note originale]({original_path})"
        logging.debug(f"[DEBUG] process_import_synthese : original_link {original_link}") 
        # Ajouter le lien au début du corps principal
        body_content = f"{original_path}\n\n{body_content}"

        # Fusionner l'entête et le contenu principal
        final_content = f"{header_content}\n\n{body_content}" if header_content else body_content
        logging.debug(f"[DEBUG] make_syntheses final_content : {final_content[:50]}")
        print(f"\nTexte final recomposé :\n{final_content[:50]}...\n")  # Aperçu limité
        # Écriture de la note reformulée
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(final_content)
        print(f"[INFO] make_syntheses a été traitée et enregistrée : {filepath}")
        logging.debug(f"[DEBUG] make_syntheses : mis à jour du fichier")
        return
    except Exception as e:
        print(f"[ERREUR] make_syntheses : Impossible de traiter : {e}")    
            
            
def get_prompt_name(category, subcategory, note_paths):
    """
    Récupère le nom du prompt basé sur la catégorie et la sous-catégorie de manière sécurisée.
    """
    logging.debug(f"[DEBUG] get_prompt_name")
    for details in note_paths.values():
        # Vérifie que les clés nécessaires existent avant de comparer
        if details.get("category") == category and details.get("subcategory") == subcategory:
            return details.get("prompt_name", None)
    return None  # Retourne None si aucune correspondance