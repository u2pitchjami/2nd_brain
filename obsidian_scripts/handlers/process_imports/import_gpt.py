from handlers.process.large_note import process_large_note
from handlers.process.ollama import ollama_generate
from handlers.process.headers import make_properties
from handlers.process.keywords import process_and_update_file
from handlers.utils.divers import read_note_content, clean_content
from handlers.utils.files import copy_file_with_date, move_file_with_date, make_relative_link, copy_to_archives
from handlers.process.prompts import PROMPTS
from datetime import datetime
import logging
import re
from pathlib import Path
from handlers.process_imports.import_syntheses import process_import_syntheses

logger = logging.getLogger()

def process_clean_gpt(filepath):
    logging.debug(f"[DEBUG] démarrage du process_clean_gpt pour : {filepath}")
    copy_file_with_date(filepath, sav_dir)
    content = read_note_content(filepath)
        
        
    logging.debug(f"[DEBUG] process_clean_gpt : envoie vers clean content {filepath}")
    content = clean_content(content, filepath)
    entry_type = "gpt_reformulation"
    logging.debug(f"[DEBUG] process_clean_gpt : prompt {entry_type}")
    prompt = PROMPTS[entry_type].format(content=content) 
    logging.debug(f"[DEBUG] process_clean_gpt : {prompt[:50]}")

    logging.debug(f"[DEBUG] process_clean_gpt : envoie vers ollama")    
    response = ollama_generate(prompt)
    logging.debug(f"[DEBUG] process_clean_gpt : reponse {response[:50]}")
    
    with open(filepath, 'w', encoding='utf-8') as file:
            file.write(response)
        
def process_import_gpt(filepath):
    """
    Traite toutes les notes dans gpt_import, en les découpant si la ligne 1 contient un titre.
    """
    logging.debug(f"[DEBUG] démarrage du process_import_gpt pour : {filepath}")
     # Définition des chemins sur le serveur Unraid
    gpt_import_dir = Path("/mnt/user/Documents/Obsidian/notes/gpt_import")
    gpt_output_dir = Path("/mnt/user/Documents/Obsidian/notes/gpt_output")

    # Vérifier et créer les dossiers si nécessaire
    if not gpt_import_dir.exists():
        gpt_import_dir.mkdir(parents=True, exist_ok=True)
        print(f"Création du dossier gpt_import à : {gpt_import_dir}")
    if not gpt_output_dir.exists():
        gpt_output_dir.mkdir(parents=True, exist_ok=True)
        print(f"Création du dossier gpt_output à : {gpt_output_dir}")
            
    gpt_import_dir = Path(gpt_import_dir)
    logging.debug(f"[DEBUG] process_import_gpt input : {gpt_import_dir}")
    gpt_output_dir = Path(gpt_output_dir)
    gpt_output_dir.mkdir(parents=True, exist_ok=True)
    logging.debug(f"[DEBUG] process_import_gpt output : {gpt_output_dir}")
    processed_count = 0
    ignored_count = 0


    for file in gpt_import_dir.glob("*.md"):
        logging.debug(f"[DEBUG] process_import_gpt : file : {file}")
        if is_ready_for_split(file):  # Vérifie si la première ligne est prête
            logging.info(f"Traitement du fichier : {file}")
            logging.debug(f"[DEBUG] process_import_gpt : ready_for split TRUE {file}")
            try:
                process_gpt_conversation(file, gpt_output_dir, prefix="GPT_Conversation")
                processed_count += 1
            except Exception as e:
                logging.error(f"Erreur lors du traitement du fichier {file} : {e}")
            
            #mouvement :
            move_file_with_date(file, "/mnt/user/Documents/Obsidian/notes/.sav/")
            logging.debug(f"[DEBUG] process_import_gpt : déplacement ")
        else:
            logging.info(f"Note ignorée, pas prête pour le découpage : {file}")
            ignored_count += 1
    logging.info(f"Fichiers traités : {processed_count}")
    logging.info(f"Fichiers ignorés : {ignored_count}")       


def is_ready_for_split(filepath):
    """
    Vérifie si la première ligne d'une note contient un titre #.
    """
    logging.debug(f"[DEBUG] is_ready_for_split {filepath}")
    with open(filepath, "r", encoding="utf-8") as file:
        first_line = file.readline().strip()  # Lire la première ligne et enlever les espaces
        logging.debug(f"[DEBUG] is_ready_for_split {first_line}")
    return first_line.startswith("# ")  # Retourne True si la ligne commence par #

def process_gpt_conversation(filepath, output_dir, prefix="GPT_Conversation"):
    """
    Traite une conversation GPT uniquement si la première ligne est un titre.
    """
    logging.debug(f"[DEBUG] process_gpt_conversation {filepath}")
    if not is_ready_for_split(filepath):
        logging.debug(f"[DEBUG] process_gpt_conversation re test is NOT ready for split")
        print(f"Note ignorée, pas de titre en ligne 1 : {filepath}")
        return  # Ignorer la note si pas prête

    with open(filepath, "r", encoding="utf-8") as file:
        content = file.read()

    # Découper la conversation en sections
    logging.debug(f"[DEBUG] process_gpt_conversation ENVOI VERS split_gpt_conversation")
    sections = split_gpt_conversation(content)

    # Créer le répertoire de sortie si nécessaire
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for title, body in sections:
        # Générer un nom de fichier à partir du titre
        safe_title = re.sub(r'[^\w\s-]', '_', title)  # Remplacer les caractères spéciaux
        filename = f"{prefix}_{safe_title}.md"
        logging.debug(f"[DEBUG] process_gpt_conversation filename {filename}")
        filepath = output_dir / filename

        # Sauvegarder la section
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(f"# {title}\n\n{body}")
        print(f"Section sauvegardée : {filepath}")
        
def split_gpt_conversation(content):
    """
    Découpe une conversation GPT en sections basées sur les titres de niveau #.
    """
    logging.debug(f"[DEBUG] split_gpt_conversation")
    # Utiliser une regex pour détecter les titres de niveau #
    sections = re.split(r'(?m)^# (.+)$', content)
    logging.debug(f"[DEBUG] split_gpt_conversation : sections : {sections[:5]}")
    # La première section (avant le premier titre) peut être ignorée si vide
    results = []
    for i in range(1, len(sections), 2):  # Sauter par 2 : Titre / Contenu
        title = sections[i].strip()
        body = sections[i + 1].strip()
        results.append((title, body))
    
    return results

def process_class_gpt(filepath, category, subcategory):
    logging.debug(f"[DEBUG] démarrage du process_clean_gpt pour : {filepath}")
    
    content = read_note_content(filepath)
        
        
    process_and_update_file(filepath)
    content = read_note_content(filepath)
    logging.debug(f"[DEBUG] content : {content}")
    
    process_import_syntheses(filepath, category, subcategory)
    make_properties(content, filepath, category, subcategory)
    
    return