import os
from handlers.prompts import PROMPTS
from handlers.ollama import ollama_generate
import logging

def determine_max_words(filepath):
    """Détermine dynamiquement la taille des blocs en fonction du fichier."""
    if "gpt_import" in filepath.lower():
        return 1000  # Petits blocs pour les fichiers importants
    else:
        return 500  # Taille par défaut

def split_large_note(content, entry_type, max_words=1000):
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

def process_large_note(content, filepath):
    logging.debug(f"[DEBUG] entrée process_large_note")
    """
    Traite une note volumineuse en la découpant et en envoyant les blocs au modèle.
    """
    max_words = determine_max_words(filepath)
    print(f"Fichier : {filepath}, Taille des blocs : {max_words}")
    
    try:
        #with open(filepath, 'r', encoding='utf-8') as file:
        #    content = file.read()

        # Étape 1 : Découpage en blocs optimaux
        blocks = split_large_note(content, max_words=max_words)
        print(f"[INFO] La note a été découpée en {len(blocks)} blocs.")
        logging.debug(f"[DEBUG] process_large_note : {len(blocks)} blocs")
        # Obtenir le dossier contenant le fichier
        base_folder = os.path.dirname(filepath)

        # Vérifie si le fichier vient de 'gpt_import'
                    
        processed_blocks = []
        for i, block in enumerate(blocks):
            print(f"[INFO] Traitement du bloc {i + 1}/{len(blocks)}...")
            logging.debug(f"[DEBUG] process_large_note : Traitement du bloc {i + 1}/{len(blocks)}")
            if "gpt_import" in base_folder:
                logging.debug(f"[DEBUG] process_large_note : prompt title")
                prompt = PROMPTS["title"].format(content=block)
            else:
                logging.debug(f"[DEBUG] process_large_note : prompt reformulation")
                prompt = PROMPTS["reformulation"].format(content=block) 
            
            logging.debug(f"[DEBUG] process_large_note : envoie vers ollama")    
            response = ollama_generate(prompt)
            logging.debug(f"[DEBUG] process_large_note : retour ollama, récupération des blocs")
            processed_blocks.append(response.strip())

        # Étape 3 : Fusionner les blocs reformulés
        logging.debug(f"[DEBUG] process_large_note : fusion des blocs")
        final_content = "\n\n".join(processed_blocks)
        #print ("final content :",final_content)
        # Écriture de la note reformulée
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(final_content)
        print(f"[INFO] La note volumineuse a été traitée et enregistrée : {filepath}")
        logging.debug(f"[DEBUG] process_large_note : mis à jour du fichier")

    except Exception as e:
        print(f"[ERREUR] Impossible de traiter {filepath} : {e}")