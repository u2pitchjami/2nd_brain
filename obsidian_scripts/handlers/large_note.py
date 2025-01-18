import os
from handlers.prompts import PROMPTS
from handlers.ollama import ollama_generate
from handlers.extract_yaml_header import extract_yaml_header
import logging
from handlers.files import copy_file_with_date

def determine_max_words(filepath):
    """Détermine dynamiquement la taille des blocs en fonction du fichier."""
    if "gpt_import" in filepath.lower():
        return 1000  # Petits blocs pour les fichiers importants
    else:
        return 1000  # Taille par défaut

def split_large_note(content, max_words=1000):
    logging.debug(f"[DEBUG] entrée split_large_note")
    """
    Découpe une note en blocs de taille optimale (max_words).
    """
    words = content.split()
    blocks = []
    current_block = []

    for word in words:
        current_block.append(word)
        if len(current_block) >= max_words:
            blocks.append(" ".join(current_block))
            current_block = []

    # Ajouter le dernier bloc s'il reste des mots
    if current_block:
        blocks.append(" ".join(current_block))

    return blocks

def process_large_note(content, filepath, entry_type):
    logging.debug(f"[DEBUG] entrée process_large_note")
    """
    Traite une note volumineuse en la découpant et en envoyant les blocs au modèle.
    """
    print(type(content))  # Vérifie le type de la variable
    max_words = determine_max_words(filepath)
    print(f"Fichier : {filepath}, Taille des blocs : {max_words}")
    logging.debug(f"[DEBUG] Type de content avant extract_yaml_header : {type(content)}")
    logging.debug(f"[DEBUG] Contenu brut avant extract_yaml_header : {repr(content[:100])}")
    try:
        #with open(filepath, 'r', encoding='utf-8') as file:
        #    content = file.read()
        # Extraire l'entête YAML
              
        header_lines, content_lines = extract_yaml_header(content)

        print(f"[DEBUG] large_note : Type de header_lines : {type(header_lines)}")  # <class 'list'>
        print(f"[DEBUG] large_note : Type de content_lines : {type(content_lines)}")  # <class 'str'>

        # Tu peux maintenant utiliser content_lines comme une chaîne
        #lines = content_lines.strip().split("\n")
        #print(lines[:5])  # Aperçu des premières lignes
        content = content_lines
    
        # Étape 1 : Découpage en blocs optimaux
        blocks = split_large_note(content, max_words=max_words)
        print(f"[INFO] La note a été découpée en {len(blocks)} blocs.")
        logging.debug(f"[DEBUG] process_large_note : {len(blocks)} blocs")
        # Obtenir le dossier contenant le fichier
        base_folder = os.path.dirname(filepath)

        
                    
        processed_blocks = []
        for i, block in enumerate(blocks):
            print(f"[INFO] Traitement du bloc {i + 1}/{len(blocks)}...")
            logging.debug(f"[DEBUG] process_large_note : Traitement du bloc {i + 1}/{len(blocks)}")
            logging.debug(f"[DEBUG] process_large_note : prompt {entry_type}")
            prompt = PROMPTS[entry_type].format(content=block) 
            
            logging.debug(f"[DEBUG] process_large_note : envoie vers ollama")    
            response = ollama_generate(prompt)
            logging.debug(f"[DEBUG] process_large_note : retour ollama, récupération des blocs")
            processed_blocks.append(response.strip())

        
        # Recomposer le résultat final
        # Calcul du nombre total de mots
        combined_text = " ".join(processed_blocks)
        total_words = len(combined_text.split())
        logging.debug(f"[DEBUG] process_large_note : nb words processed_blocks test avant repasse {total_words}")
        logging.debug(f"[DEBUG] process_large_note : REPASSE")
        

        # Étape 3 : Fusionner les blocs reformulés
        logging.debug(f"[DEBUG] process_large_note entete : {header_lines} ")
        logging.debug(f"[DEBUG] process_large_note : fusion des blocs")
        final_content = "\n".join(header_lines) + "\n\n" if header_lines else ""
        final_content += "\n".join(processed_blocks)
        logging.debug(f"[DEBUG] process_large_note : {len(blocks)} blocs")
        print(f"\nTexte final recomposé :\n{final_content[:100]}...\n")  # Aperçu limité
        # Écriture de la note reformulée
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(final_content)
        print(f"[INFO] La note volumineuse a été traitée et enregistrée : {filepath}")
        logging.debug(f"[DEBUG] process_large_note : mis à jour du fichier")
        copy_file_with_date(filepath, "/mnt/user/Documents/Obsidian/notes/.sav")
        copy_file_with_date(filepath, "/mnt/user/Documents/Obsidian/notes/.1")

    except Exception as e:
        print(f"[ERREUR] Impossible de traiter {filepath} : {e}")