from handlers.ollama import ollama_generate
import os
import logging

logger = logging.getLogger(__name__)

def create_split_notes(filepath, sections):
    logging.debug(f"[DEBUG] démarrage du create_split_notes")
    """
    Crée un fichier Markdown pour chaque section découpée.
    
    Arguments :
    - filepath : Chemin du fichier original (pour récupérer le dossier de sortie).
    - sections : Liste des sections extraites du contenu.
    """
    # Récupère le répertoire de base où les fichiers seront créés
    base_dir = os.path.dirname(filepath)

    for idx, section in enumerate(sections):
        # Définir un titre par défaut basé sur l'index
        title = f"section_{idx + 1}"

        # Si la section commence par ## ou ###, utiliser le titre Markdown
        if section.startswith("##") or section.startswith("###"):
            title = section.split("\n")[0].strip("# ").strip()

        # Générer le nom du fichier
        filename = f"{title.replace(' ', '_').lower()}.md"
        filepath_new = os.path.join(base_dir, filename)

        logging.debug(f"[DEBUG] Création de la section : {title}, Fichier : {filepath_new}")

        # Sauvegarder la section dans un nouveau fichier
        try:
            with open(filepath_new, 'w', encoding='utf-8') as new_file:
                new_file.write(section)
            logging.info(f"[INFO] Fichier créé : {filepath_new}")
        except Exception as e:
            logging.error(f"[ERREUR] Impossible de créer le fichier {filepath_new} : {e}")

    #try:
        # Supprimer la note d'origine
    #    os.remove(filepath)
    #    print(f"[SUPPRIMÉE] Note d'origine : {filepath}")
    #except Exception as e:
    #    print(f"[ERREUR] Impossible de supprimer {filepath} : {e}")
    
def should_split_note(filepath, content, min_lines=100):
    logging.debug(f"[DEBUG] démarrage should_split_note")
    lines = content.splitlines()
    word_count = len(content.split())
    char_count = len(content)
    logging.debug(f"[DEBUG] should_split_note file : {filepath} lines : {len(lines)} words : {word_count} char_count : {char_count}")
    

    return len(lines) >= min_lines

def split_note_by_subject(content):
    """
    Utilise le modèle pour détecter les changements de sujet dans une note
    et la découper en sections.
    """
    prompt = """
    You are a text analysis assistant. Your task is to read the following document and split it into separate sections whenever you detect a change in subject. 

    For each section:
    1. Provide a short title summarizing the section's main topic.
    2. Extract the section's content.

    Return the result in the following format:
    ---
    Title: <Short title summarizing the topic>
    Content: <Content of the section>
    ---

    Example:
    Input:
    1. Introduction to Python programming.
    2. Explanation of Python data types.
    3. Discussion about Python loops and conditions.

    Output:
    ---
    Title: Introduction to Python programming
    Content: 1. Introduction to Python programming.
    ---

    Title: Explanation of Python data types
    Content: 2. Explanation of Python data types.
    ---

    Title: Discussion about Python loops and conditions
    Content: 3. Discussion about Python loops and conditions.
    ---

    Now process the following text:
    {content}
    """
    response = ollama_generate(prompt.format(content=content))
    return response.strip()