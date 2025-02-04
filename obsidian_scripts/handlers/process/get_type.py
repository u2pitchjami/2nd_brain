"""
Ce module permet de définir la categ/sous categ d'une note.
"""
import shutil
import json
import os
import re
import logging
from datetime import datetime
from pathlib import Path
from Levenshtein import ratio
from handlers.process.ollama import ollama_generate
from handlers.utils.extract_yaml_header import extract_yaml_header
from handlers.process.prompts import PROMPTS
from handlers.utils.process_note_paths import load_note_paths, get_path_from_classification, save_note_paths
from handlers.utils.extract_yaml_header import extract_category_and_subcategory

logger = logging.getLogger()

similarity_warnings_log = os.getenv('SIMILARITY_WARNINGS_LOG')
uncategorized_log = os.getenv('UNCATEGORIZED_LOG')
uncategorized_path = Path(os.getenv('UNCATEGORIZED_PATH'))
uncategorized_path.mkdir(parents=True, exist_ok=True)


def process_get_note_type(filepath):
    """Analyse le type de note via Llama3.2."""
    logging.debug("[DEBUG] entrée process_get_note_type")

    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()
    try:
        note_paths = load_note_paths()
        _, content_lines = extract_yaml_header(content)
        subcateg_dict = generate_optional_subcategories()
        categ_dict = generate_categ_dictionary()
        entry_type = "type"
        # Construire le prompt
        prompt = PROMPTS[entry_type].format(categ_dict=categ_dict,
                    subcateg_dict=subcateg_dict, content=content_lines[:1000])

        # Appel à l'API de Llama3.2
        logging.debug("[DEBUG] process_get_note_type : %s", prompt)
        response = ollama_generate(prompt)
        logging.debug("[DEBUG] process_get_note_type response : %s", response)
        # Récupération et traitement de la réponse
        parse_category = parse_category_response(response)
        logging.debug("[DEBUG] process_get_note_type parse_category %s", parse_category)
        note_type = clean_note_type(parse_category)

        logging.info("Type de note détecté pour %s : %s", filepath, note_type)
    except Exception as e:
        logging.error("Erreur lors de l'analyse : %s", e)
        raise ValueError("Erreur détectée dans le traitement") from e

    dir_type_name = get_path_safe(note_type, filepath)
    if dir_type_name is None:
        # Cas où la note est déplacée dans 'uncategorized'
        logging.warning(
            "La note %s a été déplacée dans 'uncategorized'. Aucune action nécessaire."
            , filepath)
        return None# Arrêter le traitement ici pour ce fichier

# Continuer le traitement avec un chemin valide
    try:
        dir_type_name = Path(dir_type_name)
        dir_type_name.mkdir(parents=True, exist_ok=True)
        logging.debug("[DEBUG] dirtype_name %s", type(dir_type_name))
        logging.info("[INFO] Catégorie définie %s", dir_type_name)
    except Exception as e:
        logging.error("[ERREUR] Anomalie lors du process de Categorisation : %s", e)
        raise

    try:
        new_path = shutil.move(filepath, dir_type_name)
        logging.info("[INFO] note déplacée vers : %s", new_path)
        return new_path
    except Exception as e:
        logging.error("[ERREUR] Pb lors du déplacement : %s", e)
        raise

def parse_category_response(response):
    """
    Extrait la catégorie et sous-catégorie d'une réponse au format 'categ/souscateg'
    """
    pattern = r'([A-Za-z0-9_ ]+)/([A-Za-z0-9_ ]+)'  # Capture 'categ/souscateg'

    match = re.search(pattern, response)
    if match:
        category = match.group(1).strip()
        subcategory = match.group(2).strip()
        return f"{category}/{subcategory}"

    return "Uncategorized"


def clean_note_type(response):
    """
    Supprimer les guillemets et mettre en minuscule
    """
    logging.debug("[DEBUG] clean_note_type : %s", response)
    clean_str = response.strip().lower().replace('"', '').replace("'", '')

    # Remplacer les espaces par des underscores
    clean_str = clean_str.replace(" ", "_")

    # Supprimer les caractères interdits pour un nom de dossier/fichier
    clean_str = re.sub(r'[\:*?"<>|]', '', clean_str)

    # Supprimer un point en fin de nom (interdit sous Windows)
    clean_str = re.sub(r'\.$', '', clean_str)
    logging.debug("[DEBUG] clean_note_type : %s", clean_str)
    return clean_str

def generate_classification_dictionary():
    """
    Génère la section 'Classification Dictionary' du prompt à partir de NOTE_PATHS.
    :param note_paths: Dictionnaire NOTE_PATHS
    :return: Texte formaté pour le dictionnaire
    """
    note_paths = load_note_paths()
    logging.debug("[DEBUG] generate_classification_dictionary")
    classification_dict = "Classification Dictionary:\n"
    categories = {}

    for _, value in note_paths.items():
        category = value["category"]
        subcategory = value["subcategory"]
        explanation = value.get("explanation", "No description available.")

        if category not in categories:
            categories[category] = []
        categories[category].append(f'  - "{subcategory}": {explanation}')

    for category, subcategories in categories.items():
        classification_dict += f'- "{category}":\n' + "\n".join(subcategories) + "\n"

    return classification_dict

def generate_optional_subcategories():
    """
    Génère uniquement la liste des sous-catégories disponibles, 
    en excluant les catégories sans sous-catégories.
    
    :param note_paths: Dictionnaire contenant les informations des notes.
    :return: Texte formaté avec les sous-catégories optionnelles.
    """
    logging.debug("[DEBUG] generate_optional_subcategories")
    subcateg_dict = "Optional Subcategories:\n"
    subcategories = {}

    note_paths = load_note_paths()
    for _, value in note_paths.items():
        category = value["category"]
        subcategory = value.get("subcategory", None)

        if subcategory:  # 🔹 Ignore les sous-catégories nulles ou vides ("")
            if category not in subcategories:
                subcategories[category] = set()
            subcategories[category].add(subcategory)

    # Vérifier s'il y a des sous-catégories avant d'afficher
    if subcategories:
        for category, subcateg_list in subcategories.items():
            subcateg_dict += f'- "{category}": {", ".join(sorted(subcateg_list))}\n'
    else:
        return ""  # 🔹 Retourne une chaîne vide si aucune sous-catégorie n'est trouvée

    return subcateg_dict

def generate_categ_dictionary():
    """
    Génère la section 'Classification Dictionary' du prompt à partir de NOTE_PATHS,
    en excluant les catégories ayant une sous-catégorie
    et en affichant l'explication sur la même ligne.
    :param note_paths: Dictionnaire contenant les chemins de notes et leurs informations.
    :return: Texte formaté ne contenant que les catégories sans sous-catégories.
    """
    note_paths = load_note_paths()
    logging.debug("[DEBUG] generate_categ_dictionary")
    categ_dict = "Categ Dictionary:\n"
    categories = {}

    # Regroupement des explications uniquement pour les catégories sans sous-catégorie
    for _, value in note_paths.items():
        category = value["category"]
        subcategory = value.get("subcategory", None)  # Vérifie si une sous-catégorie existe
        explanation = value.get("explanation", "No description available.")

        # On ne prend en compte que les catégories sans sous-catégorie
        if subcategory is None:
            if category not in categories:
                categories[category] = explanation  # On garde UNE explication (la première trouvée)

    # Formatage du texte de sortie
    for category, explanation in categories.items():
        categ_dict += f'- "{category}": {explanation}\n'

    return categ_dict

# Trouver ou créer un chemin
def get_path_safe(note_type, filepath):
    """
    chercher et créer le chemin si besoin.
    """
    logging.debug("entrée get_path_safe avec note_type: %s", note_type)
    note_paths = load_note_paths()
    try:
        category, subcategory = note_type.split("/")
        try:
            return get_path_from_classification(category, subcategory)
        except KeyError:
            logging.info("Sous-catégorie absente : %s. Vérification de la validité...", subcategory)
            existing_subcategories = [
                details["subcategory"]
                for details in note_paths.values()
                if details["category"] == category
            ]
            validated_subcategory = check_and_handle_similarity(subcategory, existing_subcategories)
            if validated_subcategory is None:
                # Cas douteux : basculer en uncategorized
                logging.debug("get_path_safe: uncategorized")
                handle_uncategorized(filepath, note_type, llama_proposition=subcategory)
                return None
            if validated_subcategory == subcategory:
                logging.debug("get_path_safe: %s == %s", validated_subcategory, subcategory)
                # Nouvelle sous-catégorie validée
                return add_dynamic_subcategory(category, subcategory)

            # Fusion avec une sous-catégorie existante
            return get_path_from_classification(category, validated_subcategory)
    except ValueError:
        logging.error("Format inattendu du résultat Llama : %s", note_type)
        handle_uncategorized(filepath, note_type, llama_proposition="Invalid format")
        return None


# Ajouter une sous-catégorie dynamiquement
def add_dynamic_subcategory(category, subcategory):
    """
    Ajoute une sous-catégorie à une catégorie existante
    (uniquement si elle n'a pas déjà une sous-catégorie).
    :param category: Nom de la catégorie principale.
    :param subcategory: Nom de la sous-catégorie à ajouter.
    :param note_paths: Dictionnaire contenant les catégories et leurs chemins.
    :return: Le chemin de la nouvelle sous-catégorie.
    """
    note_paths = load_note_paths()
    base_path = None
    logging.debug("[DEBUG] add_dynamic_subcategory")

    # 🔹 Recherche de la catégorie avec subcategory=None
    for _, details in note_paths.items():
        logging.debug("[DEBUG] Détails de la catégorie : %s", details["category"])
        if details["category"].lower() == category.lower() and details.get("subcategory") is None:
            base_path = Path(details["path"])  # Utilisation de pathlib pour plus de robustesse
            break

    if not base_path:
        raise ValueError(f"[❌] Catégorie inconnue ou déjà avec sous-catégorie : {category}")

    # 🔹 Création du chemin pour la nouvelle sous-catégorie
    new_subcategory_name = subcategory.capitalize()
    new_path = base_path / new_subcategory_name

    # 🔹 Création physique du dossier si inexistant
    if not new_path.exists():
        logging.info("[INFO] Création du dossier : %s", new_path)
        new_path.mkdir(parents=True, exist_ok=True)

    # 🔹 Construction de la clé pour note_paths.json
    new_key = f"{base_path.relative_to('/mnt/user/Documents/Obsidian/notes')}/{new_subcategory_name}"
    
    note_paths[new_key] = {
        "category": category.lower(),
        "subcategory": subcategory.lower(),
        "path": str(new_path),  # Assurer que le chemin est converti en string pour JSON
        "prompt_name": "divers",
        "explanation": f"Note about {subcategory.lower()}",
        "folder_type": "storage"
    }

    # 🔹 Sauvegarde du fichier JSON (en supposant une fonction existante `save_note_paths`)
    save_note_paths(note_paths)

    return new_path

# Gérer les notes non catégorisées
def handle_uncategorized(filepath, note_type, llama_proposition):
    """
    création de logs pour les fichier uncategorized.
    """
    new_path = uncategorized_path / Path(filepath).name
    shutil.move(filepath, new_path)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(uncategorized_log, "a", encoding='utf-8') as log_file:
        log_file.write("Date: %s \n", current_time)
        log_file.write("Note: %s \n", new_path)
        log_file.write("Proposition Llama3.2: %s \n", llama_proposition)
        log_file.write("Note type original: %s \n", note_type)
        log_file.write("-" * 50 + "\n")
    logging.warning("Note déplacée vers 'uncategorized' : %s", new_path)

# Vérification des similarités avec Levenshtein
def find_similar_levenshtein(
    subcategory, existing_subcategories, threshold_low=0.7):
    """
    Vérifie les similarités.
    """
    similar = []
    for existing in existing_subcategories:
        similarity = ratio(subcategory, existing)
        logging.debug("find_similar_levenshtein similarity : %s %s", subcategory, similarity)
        if similarity >= threshold_low:
            similar.append((existing, similarity))
    return sorted(similar, key=lambda x: x[1], reverse=True)

# Gérer les similarités
def check_and_handle_similarity(
    new_subcategory, existing_subcategories, threshold_low=0.7):
    """
    Vérifie les similarités pour une nouvelle sous-catégorie et applique une logique automatique.
    """
    threshold_high = 0.9
    similar = find_similar_levenshtein(
        new_subcategory, existing_subcategories, threshold_low)
    logging.debug("check_and_handle_similarity similar : %s", similar)
    if similar:
        closest, score = similar[0]
        if score >= threshold_high:
            # Fusion automatique si la similarité est très élevée
            logging.info("Fusion automatique : %s -> %s (score: %.2f)"
                         , new_subcategory, closest, score)
            return closest
        if threshold_low <= score < threshold_high:
            # Loguer les similarités moyennes et NE PAS créer la sous-catégorie
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_message = (
                f"[{current_time}] Doute : '{new_subcategory}' proche de '{closest}'"
                f"(score: {score:.2f})\n")

            logging.warning(
            "Similitude moyenne détectée : '%s' proche de '%s' (score: %.2f)",
            new_subcategory,
            closest,
            score
            )
            with open(similarity_warnings_log, "a", encoding='utf-8') as log_file:
                log_file.write(log_message)
            return None  # Retourne None pour éviter la création
    # Si aucune similarité significative, considérer comme nouvelle sous-catégorie
    return new_subcategory
