import yaml
import re
import logging
from pathlib import Path
import shutil
import os
from difflib import get_close_matches
from handlers.process.get_type import extract_category_and_subcategory, get_path_from_classification, load_note_paths, get_path_by_category_and_subcategory, categ_extract
from handlers.process.headers import add_metadata_to_yaml
from handlers.process_imports.import_syntheses import process_import_syntheses
from handlers.utils.files import make_relative_link
from handlers.process.extract_yaml_header import extract_yaml_header

logger = logging.getLogger()

note_paths_file = os.getenv('NOTE_PATHS_FILE')
NOTE_PATHS = load_note_paths(note_paths_file)
note_paths = NOTE_PATHS

def validate_category_and_subcategory(category, subcategory, note_paths):
    """
    Valide la catégorie et sous-catégorie en les comparant avec NOTE_PATHS.
    Renvoie le chemin attendu en cas de succès, sinon None.
    """
    for key, info in note_paths.items():
        if info["category"] == category and info["subcategory"] == subcategory:
            return info["path"]
    # Recherche d'une correspondance approximative pour la catégorie
    closest_category = get_close_matches(category, [info["category"] for info in note_paths.values()], n=1, cutoff=0.8)
    closest_subcategory = get_close_matches(subcategory, [info["subcategory"] for info in note_paths.values()], n=1, cutoff=0.8)
    
    if closest_category or closest_subcategory:
        logging.warning(f"[ATTENTION] Correction suggérée : "
                        f"category={closest_category[0] if closest_category else category}, "
                        f"subcategory={closest_subcategory[0] if closest_subcategory else subcategory}")
        return None

    logging.error(f"[ERREUR] Catégorie ou sous-catégorie invalide : {category}/{subcategory}")
    return None

def verify_and_correct_category(filepath):
    """
    Vérifie et corrige la catégorie d'une synthèse, en déplaçant et modifiant si nécessaire.
    """
    try:
        # Extraire la catégorie et sous-catégorie
        category, subcategory = extract_category_and_subcategory(filepath)
        logging.debug(f"[DEBUG] catégorie/sous-catégorie {category} / {subcategory}")
        if not category or not subcategory:
            logging.warning(f"[ATTENTION] Impossible d'extraire catégorie/sous-catégorie pour {filepath}")
            return False

        # Valider la catégorie et sous-catégorie
        expected_path = validate_category_and_subcategory(category, subcategory, NOTE_PATHS)
        logging.debug(f"[DEBUG] validation catégorie/sous-catégorie {category} / {subcategory}")
        if not expected_path:
            logging.error(f"[ERREUR] Catégorie ou sous-catégorie non valide pour {filepath}. Opération annulée.")
            return False

        # Vérifier si le fichier est déjà dans le bon dossier
        current_path = filepath.parent.resolve()
        logging.debug(f"[DEBUG] current_path {current_path}")
        if current_path != expected_path.resolve():
            logging.debug(f"[DEBUG] current_path {current_path} != {category} / {subcategory}")
            # Récupération de l'archive
            archive_path = add_archives_to_path(filepath)
            logging.debug(f"[DEBUG] archive_path {archive_path} - {filepath}")
            if not archive_path or not archive_path.exists():
                logging.warning(f"[ATTENTION] Aucun fichier archive trouvé")
                return False

            # Modification de la catégorie dans l'archive
            with open(archive_path, "r+", encoding="utf-8") as file:
                lines = file.readlines()
                for i, line in enumerate(lines):
                    if line.startswith("category:"):
                        lines[i] = f"category: {category}\n"
                    elif line.startswith("sub category:"):
                        lines[i] = f"sub category: {subcategory}\n"
                file.seek(0)
                file.writelines(lines)
                file.truncate()

            # Déplacer le fichier au bon endroit
            new_path = expected_path / archive_path.name
            archive_path.rename(new_path)
            logging.info(f"[INFO] Fichier déplacé : {archive_path} --> {new_path}")

            # Supprimer l'ancien fichier
            filepath.unlink(missing_ok=True)

            # Lancer le processus de régénération de synthèse (appel à une fonction dédiée)
            process_import_syntheses(new_path, category, subcategory)
            logging.info(f"[INFO] Synthèse régénérée pour category={category}, subcategory={subcategory}")

            return True

        # Tout est correct
        logging.info(f"[INFO] Catégorie correcte pour {filepath}")
        return True

    except Exception as e:
        logging.error(f"[ERREUR] Échec de la vérification/correction pour {filepath} : {e}")
        return False
    
def add_archives_to_path(filepath):
    # Créer un objet Path à partir du chemin
    logging.debug("[DEBUG] add_archives_to_path %s", filepath)
    path_obj = Path(filepath)
    logging.debug("[DEBUG] add_archives_to_path path_obj : %s", path_obj)
    # Insérer "Archives" entre le dossier parent et le fichier
    archives_dir = path_obj.parent / "Archives"  # Ajouter "Archives" au dossier parent
    logging.debug("[DEBUG] add_archives_to_path archives_dir : %s", archives_dir)
    archives_dir.mkdir(parents=True, exist_ok=True)  # Créer le dossier Archives s'il n'existe pas
    
    archive_path = archives_dir / path_obj.name
    logging.debug("[DEBUG] add_archives_to_path archive_path : %s", archive_path)
    return archive_path

def process_sync_entete_with_path(filepath):
    """
    Synchronise l'entête YAML avec le chemin physique du fichier.
    """
    filepath = Path(filepath)  # Nouveau chemin
    file = filepath.name
    base_folder = filepath.parent  # Simplification avec Path
    new_category, new_subcategory = categ_extract(filepath)  # Nouvelles catégories

    logging.debug("[DEBUG] process_sync_entete_with_path %s", filepath)

    category, subcategory = extract_category_and_subcategory(filepath)  # Anciennes catégories
    logging.debug("[DEBUG] process_sync_entete_with_path %s %s", category, subcategory)
    path_src = get_path_by_category_and_subcategory(category, subcategory, note_paths)  # Ancien chemin
    logging.debug("[DEBUG] process_sync_entete_with_path %s ", path_src)
    file_path_src = path_src / file
    archives_path_src = add_archives_to_path(file_path_src)  # Ancien chemin archive
    logging.debug("[DEBUG] process_sync_entete_with_path %s ", archives_path_src)
    archives_path_dest = add_archives_to_path(filepath)  # Nouveau chemin archive
    logging.debug("[DEBUG] process_sync_entete_with_path %s ", archives_path_src)

    # Vérifier que le fichier source existe avant de copier
    if archives_path_src.exists():
        shutil.copy(archives_path_src, archives_path_dest)
        logging.info(f"[INFO] Copy réussi vers : {archives_path_dest}")
        # Supprimer l'ancien fichier archive
        archives_path_src.unlink(missing_ok=True)
    else:
        logging.warning(f"[WARN] Archive source introuvable : {archives_path_src}")

    ##### MODIF CATEG ARCHIVE
    with open(archives_path_dest, "r", encoding="utf-8") as file:
        archive_content = file.read()
    # Récupérer les valeurs existantes
    tags_existants = []
    resume_existant = []
    status_existant = ""
    yaml_header_archive, body_content_archive = extract_yaml_header(archive_content)
    logging.debug(f"[DEBUG] yaml_header_archive : {yaml_header_archive}")
    
    in_summary = False  # Pour détecter si on est dans le bloc summary

    for line in yaml_header_archive:
        if line.startswith("tags:"):
            tags_str = line.replace("tags:", "").strip()
            tags_str = tags_str.strip("[]")  # 🔥 Enlève les crochets 🔥
            tags_existants = [tag.strip() for tag in tags_str.split(",")]

        elif line.startswith("summary:"):
            in_summary = True  # On entre dans le bloc summary
            resume_existant = []  # Réinitialise la liste pour stocker le bloc de texte

        elif in_summary:
            if line.strip() == "":  # Si on rencontre une ligne vide, on sort du bloc summary
                in_summary = False
            else:
                resume_existant.append(line.strip())  # On stocke chaque ligne du summary

        elif line.startswith("status:"):
            status_existant = line.replace("status:", "").strip()

    # Reformater summary proprement en bloc de texte
    resume_existant = "\n".join(resume_existant)

    logging.debug(f"[DEBUG] Extraction terminée : Tags={tags_existants}, Summary=\n{resume_existant}, Status={status_existant}")

            
            
    # Mettre à jour l'entête avec les nouvelles catégories tout en conservant les autres valeurs
    add_metadata_to_yaml(archives_path_dest, tags_existants, resume_existant, new_category, new_subcategory, status_existant)
    ##### MODIF CATEG SYNTHESE + LIEN ARCHIVE
    with open(filepath, "r", encoding="utf-8") as file:
        content = file.read()
    archives_path_dest_relative = make_relative_link(archives_path_dest, link_text="Voir la note originale")
    update_archive_link(filepath, content, archives_path_dest_relative)
    yaml_header, body_content = extract_yaml_header(content)
    logging.debug(f"[DEBUG] Contenu actuel de yaml_header : {yaml_header}")
    # Récupérer les valeurs existantes
    tags_existants = []
    resume_existant = []
    status_existant = ""
    in_summary = False  # Pour détecter si on est dans le bloc summary

    for line in yaml_header:
        if line.startswith("tags:"):
            tags_str = line.replace("tags:", "").strip()
            tags_str = tags_str.strip("[]")  # 🔥 Enlève les crochets 🔥
            tags_existants = [tag.strip() for tag in tags_str.split(",")]

        elif line.startswith("summary:"):
            in_summary = True  # On entre dans le bloc summary
            resume_existant = []  # Réinitialise la liste pour stocker le bloc de texte

        elif in_summary:
            if line.strip() == "":  # Si on rencontre une ligne vide, on sort du bloc summary
                in_summary = False
            else:
                resume_existant.append(line.strip())  # On stocke chaque ligne du summary

        elif line.startswith("status:"):
            status_existant = line.replace("status:", "").strip()

    # Reformater summary proprement en bloc de texte
    resume_existant = "\n".join(resume_existant)
        
    # Mettre à jour l'entête avec les nouvelles catégories tout en conservant les autres valeurs
    add_metadata_to_yaml(filepath, tags_existants, resume_existant, new_category, new_subcategory, status_existant)

def update_archive_link(filepath, content, new_archive_path):
    """
    Met à jour le lien vers l'archive dans les 10 premières lignes de `content`.
    """
    pattern = r"(\[Voir la note originale\]\()(.*?)(\))"
    lines = content.splitlines()
    modified = False

    for i in range(len(lines)):  
        if re.search(pattern, lines[i]):  
            lines[i] = re.sub(pattern, rf"\1{new_archive_path}\3", lines[i])
            modified = True
            logging.info(f"[INFO] Lien mis à jour sur la ligne {i+1} avec : {new_archive_path}")
            break  

    if not modified:
        logging.warning("⚠️ Aucun lien d'archive trouvé.")

    new_content = "\n".join(lines)  # ✅ Assemble les lignes en un seul texte
    with open(filepath, "w", encoding="utf-8") as file:  # ✅ Ouvre bien le fichier
        file.write(new_content)  # ✅ Écrit le texte dans le fichier

    logging.info(f"[INFO] Lien mis à jour pour : {filepath}")  # ✅ Confirme l'action
    
    return

def dump_yaml_header(header):
    """
    Convertit un dictionnaire YAML en chaîne de caractères.
    """
    return "---\n" + yaml.dump(header, sort_keys=False) + "---\n"