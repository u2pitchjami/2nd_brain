"""
Ce module extrait les en-têtes YAML des fichiers de notes Obsidian.
"""
import logging
import re
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

def extract_category_and_subcategory(filepath):
    """
    Lit l'entête d'un fichier pour extraire la catégorie et la sous-catégorie.
    On suppose que les lignes sont au format :
    category: valeur
    subcategory: valeur
    """
    logging.debug("[DEBUG] extract_category_and_subcategory %s", filepath)
    category = None
    subcategory = None
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            for line in file:
                if line.startswith("category:"):
                    category = line.split(":")[1].strip()
                    logging.debug("[DEBUG] extract_category_and_subcategory %s", category)
                elif line.startswith("sub category:"):
                    subcategory = line.split(":")[1].strip()
            return category, subcategory
    except ValueError as e:
        logging.error("[ERREUR] Impossible de lire l'entête du fichier %s : %s", filepath, e)
        return None, None

def extract_status(filepath):
    """
    Lit l'entête d'un fichier pour extraire la catégorie et la sous-catégorie.
    On suppose que les lignes sont au format :
    category: valeur
    subcategory: valeur
    """
    status = None
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            for line in file:
                if line.startswith("status:"):
                    status = line.split(":")[1].strip()
            return status
    except FileNotFoundError as e:
        logging.error("[ERREUR] Impossible de lire l'entête du fichier %s : %s", filepath, e)
        return None

def extract_tags(yaml_header):
    tags_existants = []
    in_tags = False

    for line in yaml_header:
        stripped_line = line.strip()

        if stripped_line.startswith("tags:") and "[" in stripped_line:
            tags_str = stripped_line.replace("tags:", "").strip()
            tags_str = tags_str.strip("[]")
            tags_existants = [tag.strip() for tag in tags_str.split(",")]
            in_tags = False

        elif stripped_line.startswith("tags:") and "[" not in stripped_line:
            in_tags = True
            tags_existants = []

        elif in_tags:
            clean_line = line.lstrip()
            if clean_line.startswith("- "):
                tag = clean_line.replace("- ", "").strip()
                tags_existants.append(tag)
            elif stripped_line == "" or re.match(r"^\w+:.*$", stripped_line):
                in_tags = False

    logging.debug(f"[DEBUG] Tags extraits : {tags_existants}")
    return tags_existants

def extract_summary(yaml_header):
    resume_existant = []
    in_summary = False

    for line in yaml_header:
        stripped_line = line.strip()

        if stripped_line.startswith("summary:"):
            in_summary = True
            summary_content = stripped_line.replace("summary:", "").strip()

            if summary_content and summary_content != "|":  # Si résumé en ligne unique
                resume_existant.append(summary_content)
                in_summary = False
            elif summary_content == "|":  # Détection du résumé en bloc multi-lignes
                resume_existant = []
            else:
                in_summary = False

        elif in_summary:
            if stripped_line == "" or re.match(r"^\w+:.*$", stripped_line):  # Fin du bloc summary
                in_summary = False
            else:
                resume_existant.append(stripped_line)

    resume_existant = "\n".join(resume_existant).strip()
    logging.debug(f"[DEBUG] Résumé extrait : {resume_existant}")
    return resume_existant

def extract_metadata(yaml_header, key_to_extract=None):
    """
    Extrait les métadonnées de l'entête YAML.
    
    :param yaml_header: Liste des lignes de l'entête YAML.
    :param key_to_extract: Si spécifié, retourne uniquement la valeur de cette clé.
    :return: Dictionnaire des métadonnées ou la valeur de la clé spécifiée.
    """
    metadata = {}
    for line in yaml_header:
        stripped_line = line.strip()

        if ":" in stripped_line:
            key, value = stripped_line.split(":", 1)
            key = key.strip()
            value = value.strip()
            metadata[key] = value

    if key_to_extract:
        result = metadata.get(key_to_extract, None)
        logging.debug(f"[DEBUG] Métadonnée extraite pour '{key_to_extract}' : {result}")
        return result

    logging.debug(f"[DEBUG] Métadonnées extraites : {metadata}")
    return metadata
