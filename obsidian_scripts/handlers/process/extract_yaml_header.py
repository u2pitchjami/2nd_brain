"""
Ce module extrait les en-têtes YAML des fichiers de notes Obsidian.
"""
import logging
logger = logging.getLogger()

def extract_yaml_header(content):
    """
    Extrait l'entête YAML d'un texte s'il existe.
    
    Args:
        text (str): Le texte à analyser.
    
    Returns:
        tuple: (header_lines, content_lines)
            - header_lines : Liste contenant les lignes de l'entête YAML.
            - content_lines : Liste contenant le reste du texte sans l'entête.
    """
    logging.debug("[DEBUG] entrée extract_yaml_header")
    lines = content.strip().split("\n")  # Découpe le contenu en lignes
    if lines[0].strip() == "---":  # Vérifie si la première ligne est une délimitation YAML
        logging.debug("[DEBUG] extract_yaml_header line 0 : ---")
        yaml_start = 0
        yaml_end = next((i for i, line in enumerate(lines[1:], start=1)
                         if line.strip() == "---"), -1)
        logging.debug("[DEBUG] extract_yaml_header yalm_end : %s ", yaml_end)
        header_lines = lines[yaml_start:yaml_end + 1]  # L'entête YAML
        content_lines = lines[yaml_end + 1:]  # Le reste du contenu
    else:
        header_lines = []
        content_lines = lines  # Tout le contenu est traité comme texte

    logging.debug("[DEBUG] extract_yaml_header header : %s ", repr(header_lines))
    logging.debug("[DEBUG] extract_yaml_header content : %s ", content_lines[:5])
    # Rejoindre content_lines pour retourner une chaîne
    return header_lines, "\n".join(content_lines)
