import requests
from handlers.prompts import PROMPTS
from handlers.ollama import ollama_generate
from handlers.extract_yaml_header import extract_yaml_header
from handlers.config import NOTE_PATHS
import logging
from pathlib import Path
import shutil

logger = logging.getLogger(__name__)

def process_get_note_type(filepath):
    """Analyse le type de note via Llama3.2."""
    logging.debug(f"[DEBUG] entrée process_get_note_type")
    
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()
    try:
        header_lines, content_lines = extract_yaml_header(content)
        classification_dict = generate_classification_dictionary(NOTE_PATHS)
        #print(f"[DEBUG] process_get_note_type : Type de header_lines : {type(header_lines)}")  # <class 'list'>
        #print(f"[DEBUG] process_get_note_type : Type de content_lines : {type(content_lines)}")  # <class 'str'>
        entry_type = "type"
        # Construire le prompt
        prompt = PROMPTS[entry_type].format(classification_dict=classification_dict, content=content_lines[:1000]) 
    
    
        # Appel à l'API de Llama3.2
        logging.debug(f"[DEBUG] process_get_note_type : envoie vers ollama")    
        response = ollama_generate(prompt)
        logging.debug(f"[DEBUG] process_get_note_type : {response}")
        # Récupération et traitement de la réponse
        
        note_type = response.strip().lower()
        
        #if note_type not in VALID_TYPES:
        #    logging.warning(f"Type invalide détecté : {note_type}. Défini comme 'unknown'.")
        #    note_type = "unknown"
        
        logging.info(f"Type de note détecté pour {filepath} : {note_type}")
        
    except Exception as e:
        logging.error(f"Erreur lors de l'analyse : {e}")
        raise "erreur"
    
    dir_type_name = get_path_safe(note_type, NOTE_PATHS)
    try:
        dir_type_name = Path(dir_type_name)
        dir_type_name.mkdir(parents=True, exist_ok=True)
        logging.info(f"[INFO] Catégorie définie {dir_type_name}")
    except Exception as e:
        logging.error(f"[ERREUR] Anomalie lors du process de Categorisation : {e}")
        raise
    
    try:
        new_path = shutil.move(filepath, dir_type_name)
        logging.info(f"[INFO] note déplacée vers : {new_path}")
        return new_path
    except Exception as e:
        logging.error(f"[ERREUR] Pb lors du déplacement : {e}")
        raise
    
    
def get_path_from_classification(category, subcategory, note_paths):
    """
    Retourne le chemin associé à une catégorie et sous-catégorie dans NOTE_PATHS.
    """
    logging.debug(f"[DEBUG] get_path_from_classification : {category} {subcategory}") 
    for details in note_paths.values():
        if details["category"] == category and details["subcategory"] == subcategory:
            logging.debug(f"[DEBUG] get_path_from_classification : trouvé dans la base")
            return details["path"]
    raise  # Retourne None si aucune correspondance trouvée

def generate_classification_dictionary(note_paths):
    """
    Génère la section 'Classification Dictionary' du prompt à partir de NOTE_PATHS.
    :param note_paths: Dictionnaire NOTE_PATHS
    :return: Texte formaté pour le dictionnaire
    """
    classification_dict = "Classification Dictionary:\n"
    categories = {}

    for key, value in note_paths.items():
        category = value["category"]
        subcategory = value["subcategory"]
        explanation = value.get("explanation", "No description available.")

        if category not in categories:
            categories[category] = []
        categories[category].append(f'  - "{subcategory}": {explanation}')

    for category, subcategories in categories.items():
        classification_dict += f'- "{category}":\n' + "\n".join(subcategories) + "\n"

    return classification_dict

def get_path_safe(note_type, note_paths):
    """
    Trouve le chemin à partir du résultat Llama en toute sécurité.
    """
    logging.debug(f"entrée get_path_safe")
    try:
        category, subcategory = note_type.split("/")
        return get_path_from_classification(category, subcategory, note_paths)
    except ValueError:
        logging.error(f"Format inattendu du résultat Llama : {note_type}")
        return None
    
def categ_extract(base_folder):
    """
    Extrait la categ et sous categ de la note.
    """
    logging.debug(f"entrée categ_extract pour : {base_folder}")
    try:
        for path, details in NOTE_PATHS.items():
                logging.debug(f"[DEBUG] path : {path}")
                if path in base_folder:
                    logging.debug(f"[DEBUG] Traitement de la note pour : {path}")
                    category = details["category"]
                    subcategory = details.get("subcategory")
                    logging.debug(f"[DEBUG] categ extract : {category}/{subcategory}")
                    return category, subcategory
    except ValueError:
        logging.error(f"Catégorie introuvable")
        raise
    
def get_path_by_category_and_subcategory(category, subcategory, note_paths):
    for key, value in note_paths.items():
        if value.get("category") == category and value.get("subcategory") == subcategory:
            return value.get("path")
    return None  # Retourne None si aucune correspondance n'est trouvée

def extract_category_and_subcategory(filepath):
    """
    Lit l'entête d'un fichier pour extraire la catégorie et la sous-catégorie.
    On suppose que les lignes sont au format :
    category: valeur
    subcategory: valeur
    """
    try:
        with open(filepath, 'r') as file:
            for line in file:
                if line.startswith("category:"):
                    category = line.split(":")[1].strip()
                elif line.startswith("sub category:"):
                    subcategory = line.split(":")[1].strip()
            return category, subcategory
    except Exception as e:
        logging.error(f"[ERREUR] Impossible de lire l'entête du fichier {filepath} : {e}")
        return None, None