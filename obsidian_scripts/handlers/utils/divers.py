import re
import os
import logging

logger = logging.getLogger()

def count_words(content):
    logging.debug(f"[DEBUG] def count_word")
    return len(content.split())

def clean_content(content, filepath):
    logging.debug(f"[DEBUG] clean_content : {filepath}")
    """
    Nettoie le contenu avant de l'envoyer au modèle.
    - Conserve les blocs de code Markdown (``` ou ~~~).
    - Supprime les balises SVG ou autres éléments non pertinents.
    - Élimine les lignes vides ou répétitives inutiles.
    """
    # Supprimer les balises SVG ou autres formats inutiles
    content = re.sub(r'<svg[^>]*>.*?</svg>', '', content, flags=re.DOTALL)

    # Supprimer les lignes vides multiples
    #content = re.sub(r'\n\s*\n', '\n', content)

    # Vérifier le type et l'état final
    logging.debug(f"[DEBUG] Après nettoyage : {type(content)}, longueur = {len(content)}")
    
    return content.strip()

def read_note_content(filepath):
    """Lit le contenu d'une note depuis le fichier."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            logging.error(f"[DEBUG] lecture du fichier {filepath}")
            
            return file.read()
    except Exception as e:
        logging.error(f"[ERREUR] Impossible de lire le fichier {filepath} : {e}")
        return None