import re
import yaml
import os
import logging

# Variables globales pour les mots-clés et leur dernier horodatage
KEYWORDS_FILE = "/home/pipo/bin/dev/2nd_brain/obsidian_scripts/handlers/keywords.yaml"
TAG_KEYWORDS = {}

if os.path.exists(KEYWORDS_FILE):
    print("Fichier trouvé :", KEYWORDS_FILE)
else:
    print("Fichier introuvable :", KEYWORDS_FILE)

# Initialisation sécurisée
try:
    LAST_MODIFIED_TIME = os.path.getmtime(KEYWORDS_FILE)
except FileNotFoundError:
    LAST_MODIFIED_TIME = 0  # Valeur par défaut si le fichier n'existe pas encore


def load_keywords(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)
        
        # Transformer les mots-clés en listes
        keywords = {tag: [word.strip() for word in words.split(",")] for tag, words in raw_data.items()}
        return keywords
    except Exception as e:
        print(f"Erreur lors du chargement des mots-clés : {e}")
        raise

def process_and_update_file(filepath):
    global LAST_MODIFIED_TIME, TAG_KEYWORDS
    # Vérifier si le fichier de mots-clés a changé
    logging.debug(f"[DEBUG] process_and_update_file : vérif du fichier de mots clés is_file_update ")
    file_updated, new_modified_time = is_file_updated(KEYWORDS_FILE, LAST_MODIFIED_TIME)
    if file_updated:
        print("[INFO] Rechargement des mots-clés...")
        logging.debug(f"[DEBUG] process_and_update_file : fichier modifié : rechargement des  mots clés")
        TAG_KEYWORDS = load_keywords(KEYWORDS_FILE)
        LAST_MODIFIED_TIME = new_modified_time
    
    # Charger le contenu du fichier
    with open(filepath, 'r', encoding='utf-8') as file:
        text = file.read()
    # Charger les mots-clés depuis le fichier
    TAG_KEYWORDS = load_keywords(KEYWORDS_FILE)
    #data = yaml.safe_load(f)
    logging.debug(f"[DEBUG] Contenu du fichier YAML chargé : {TAG_KEYWORDS}")
    # Analyser les sections et générer des tags
    logging.debug(f"[DEBUG] process_and_update_file : envoie vers tag_sections")
    tagged_sections = tag_sections(text)

    # Réécrire le contenu dans le fichier
    logging.debug(f"[DEBUG] process_and_update_file : envoie vers integrate_tags_in_file")
    integrate_tags_in_file(filepath, tagged_sections)



# Surveillance des modifications du fichier
def is_file_updated(file_path, last_modified_time):
    logging.debug(f"[DEBUG] entrée dans is_file_updated")
    try:
        current_modified_time = os.path.getmtime(file_path)
        logging.debug(f"[DEBUG] is_file_updated : nouvelle date : {current_modified_time}")
        return current_modified_time != last_modified_time, current_modified_time
    except FileNotFoundError:
        print(f"[ERREUR] Fichier introuvable : {file_path}")
        return False, last_modified_time

def extract_sections(text):
    """Divise le texte en sections basées sur les titres Markdown."""
    logging.debug(f"[DEBUG] entrée fonction : extract_sections")
    sections = re.split(r'(?=^#{2,3}\s)', text, flags=re.MULTILINE)
    logging.debug(f"[DEBUG] extract_sections : {sections}")
    return [section.strip() for section in sections if section.strip()]

def detect_tags_in_text(text, TAG_KEYWORDS):
    logging.debug(f"[DEBUG] entrée fonction : detect_tags_in_text")
    """Détecte les tags dans un texte."""
    tags = set()  # Initialisation de la variable 'tags' comme un ensemble vide
    for tag, keywords in TAG_KEYWORDS.items():  # Parcourt chaque catégorie
        for keyword in keywords:  # Parcourt chaque mot-clé dans la catégorie
            if keyword.lower() in text.lower():  # Recherche insensible à la casse
                tags.add(f"#{tag}")  # Ajoute un # devant chaque tag
    return tags

def tag_sections(text):
    logging.debug(f"[DEBUG] entrée fonction : tag_sections")
    """Analyse chaque section et génère des tags basés sur le titre et le contenu."""
    logging.debug(f"[DEBUG] tag_sections : envoie vers extract_sections")
    sections = extract_sections(text)
    tagged_sections = []

    for section in sections:
        # Séparer le titre de la section du contenu
        logging.debug(f"[DEBUG] tag_sections : Séparer le titre de la section du contenu")
        title_match = re.match(r'^#{2,3}\s(.+)', section)
        title = title_match.group(1) if title_match else "Untitled Section"
        logging.debug(f"[DEBUG] tag_sections : title : {title}")
        content = section[len(title_match.group(0)):] if title_match else section

        # Chercher des tags dans le titre et le contenu
        logging.debug(f"[DEBUG] tag_sections : envoie vers detect_tags_in_text pour title_tags")
        title_tags = detect_tags_in_text(title, TAG_KEYWORDS)
        #logging.debug(f"[DEBUG] tag_sections : title_tags : {title_tags}")
        logging.debug(f"[DEBUG] tag_sections : envoie vers detect_tags_in_text pour content")
        content_tags = detect_tags_in_text(content, TAG_KEYWORDS)
        logging.debug(f"[DEBUG] tag_sections : content_tags : {content_tags}")
        all_tags = title_tags.union(content_tags)
        logging.debug(f"[DEBUG] tag_sections : all_tags : {all_tags}")
        
        # Stocker le résultat
        tagged_sections.append({
            "title": title,
            "tags": sorted(all_tags),  # Tags triés pour la lisibilité
            "content": content.strip()
        })

    return tagged_sections

def integrate_tags_in_file(filepath, tagged_sections):
    logging.debug(f"[DEBUG] entrée fonction : integrate_tags_in_file : {filepath}")
    """
    Réécrit le fichier en ajoutant les tags au début de chaque section.
    """
    with open(filepath, "r", encoding="utf-8") as file:
        lines = file.readlines()

    # Préserver l'entête YAML
    if lines[0].strip() == "---":
        yaml_start = 0
        yaml_end = next((i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---"), -1)
        header_lines = lines[yaml_start:yaml_end + 1]
        content_lines = lines[yaml_end + 1:]
    else:
        header_lines = []
        content_lines = lines

    # Loguer l'entête pour vérification
    with open(filepath, "w", encoding="utf-8") as file:
    # Écrire l'entête YAML si elle existe
        if header_lines:  # Vérifie que l'entête n'est pas vide
            file.writelines(header_lines)
            logging.debug(f"[DEBUG] integrate_tags_in_file : Entête YAML ajoutée : {''.join(header_lines)}")
    
        # Écrire les sections avec leurs titres, tags et contenu
        for section in tagged_sections:
            # Ajoute le titre de la section
            file.write(f"## {section['title']}\n")
            logging.debug(f"[DEBUG] integrate_tags_in_file : title : {section['title']} : {filepath}")
            # Ajoute les tags associés
            tags_line = " ".join(section['tags'])
            file.write(f"{tags_line}\n\n")
            logging.debug(f"[DEBUG] integrate_tags_in_file : tags : {tags_line}")
            # Ajoute le contenu de la section
            file.write(f"{section['content']}\n\n")
            logging.debug(f"[DEBUG] integrate_tags_in_file : section content : {section['content']}")
    
    print(f"Fichier mis à jour : {filepath}")