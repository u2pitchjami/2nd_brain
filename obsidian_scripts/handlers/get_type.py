import requests
from handlers.prompts import PROMPTS
from handlers.ollama import ollama_generate
from handlers.extract_yaml_header import extract_yaml_header
import logging

VALID_TYPES = ["technical", "news", "idea", "todo", "tutorial", "unknown"]

def process_get_note_type(filepath, entry_type):
    """Analyse le type de note via Llama3.2."""
    logging.debug(f"[DEBUG] entrée process_get_note_type")
    
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()
    
    header_lines, content_lines = extract_yaml_header(content)

    print(f"[DEBUG] process_get_note_type : Type de header_lines : {type(header_lines)}")  # <class 'list'>
    print(f"[DEBUG] process_get_note_type : Type de content_lines : {type(content_lines)}")  # <class 'str'>
    
    # Construire le prompt
    prompt = PROMPTS[entry_type].format(content=content_lines[:1000]) 
    
    try:
        # Appel à l'API de Llama3.2
        logging.debug(f"[DEBUG] process_get_note_type : envoie vers ollama")    
        response = ollama_generate(prompt)
        logging.debug(f"[DEBUG] process_get_note_type : {response}")
        # Récupération et traitement de la réponse
        
        note_type = response.strip().lower()
        if note_type not in VALID_TYPES:
            logging.warning(f"Type invalide détecté : {note_type}. Défini comme 'unknown'.")
            note_type = "unknown"
        
        logging.info(f"Type de note détecté pour {filepath} : {note_type}")
        return note_type
    except Exception as e:
        print(f"Erreur lors de l'analyse : {e}")
        return "erreur"