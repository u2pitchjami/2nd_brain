import os
import re
from handlers.prompts import PROMPTS
from handlers.ollama import ollama_generate
from handlers.extract_yaml_header import extract_yaml_header
import logging
from handlers.files import copy_file_with_date

logger = logging.getLogger(__name__)

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
    logging.debug(f"[DEBUG] Type de content avant extract_yaml_header : {type(content)}")
    logging.debug(f"[DEBUG] Contenu brut avant extract_yaml_header : {repr(content[:100])}")
    try:
        header_lines, content_lines = extract_yaml_header(content)
        content = content_lines
    
        # Étape 1 : Découpage en blocs optimaux
        #blocks = split_large_note(content, max_words=max_words)
        blocks = split_large_note_by_titles(content)
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
            logging.debug(f"[DEBUG] process_large_note : {prompt[:50]}")
            
            logging.debug(f"[DEBUG] process_large_note : envoie vers ollama")    
            response = ollama_generate(prompt)
            logging.debug(f"[DEBUG] process_large_note : reponse {response[:50]}")
            
            logging.debug(f"[DEBUG] process_large_note : retour ollama, récupération des blocs")
            processed_blocks.append(response.strip())

        # Vérifie et corrige les titres après traitement
        final_blocks = ensure_titles_in_blocks(processed_blocks)
                
        

        # Étape 3 : Fusionner les blocs reformulés
        # Construire l'entête (sans saut de ligne final inutile)
        header_content = "\n".join(header_lines).strip()

        # Construire le contenu principal (final_blocks)
        body_content = "\n\n".join(final_blocks).strip()

        # Fusionner l'entête et le contenu principal avec un seul saut de ligne entre les deux
        final_content = f"{header_content}\n\n{body_content}" if header_content else body_content
        logging.debug(f"[DEBUG] process_large_note : {len(blocks)} blocs")
        print(f"\nTexte final recomposé :\n{final_content[:100]}...\n")  # Aperçu limité
        # Écriture de la note reformulée
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(final_content)
        print(f"[INFO] La note volumineuse a été traitée et enregistrée : {filepath}")
        logging.debug(f"[DEBUG] process_large_note : mis à jour du fichier")
        

    except Exception as e:
        print(f"[ERREUR] Impossible de traiter {filepath} : {e}")
        
        
def split_large_note_by_titles(content):
    """
    Découpe une note en blocs basés sur les titres (#, ##, ###), 
    en gérant une éventuelle introduction avant le premier titre.
    Chaque bloc contient le titre et son contenu concaténés.
    """
    # Expression régulière pour détecter les titres
    title_pattern = r'(?m)^(\#{1,3})\s+.*$'
    
    # Trouver toutes les correspondances (positions et contenu)
    matches = list(re.finditer(title_pattern, content))
    logging.debug(f"[DEBUG] Titres trouvés : {[match.group() for match in matches]}")
    
    blocks = []
    last_pos = 0  # Position de début du dernier bloc
    
    # Gestion de l'introduction avant le premier titre
    if matches and matches[0].start() > 0:
        intro = content[:matches[0].start()].strip()
        logging.debug(f"[DEBUG] Introduction détectée : {intro[:50]}")
        if intro:
            blocks.append(f"## **Introduction**\n\n{intro}")
    
    # Découpage basé sur les titres
    for i, match in enumerate(matches):
        title = match.group().strip()  # Le titre complet (ex. : "# Section")
        start_pos = match.end()  # Fin du titre
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        
        # Extraire le contenu de la section
        section_content = content[start_pos:end_pos].strip()
        blocks.append(f"{title}\n{section_content}")
    
    return blocks

def ensure_titles_in_blocks(blocks, default_title="# Introduction"):
    """
    Vérifie que chaque bloc commence par un titre Markdown valide.
    Ajoute un titre par défaut si nécessaire.
    """
    processed_blocks = []
    
    for i, block in enumerate(blocks):
        # Vérifier si le bloc commence par un titre Markdown
        if not block.strip().startswith("#"):
            logging.debug(f"[DEBUG] Bloc sans titre détecté : {block[:30]}...")
            # Ajouter un titre par défaut
            title = default_title if i == 0 else f"# Section {i + 1}"
            block = f"{title}\n{block.strip()}"
            logging.debug(f"[DEBUG] Block : {block[:30]}...")
        processed_blocks.append(block)
    
    return processed_blocks