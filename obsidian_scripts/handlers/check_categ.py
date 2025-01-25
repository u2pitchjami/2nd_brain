from handlers.config import NOTE_PATHS
from handlers.get_type import extract_category_and_subcategory
from handlers.get_type import get_path_from_classification
from handlers.import_syntheses import process_import_syntheses
import logging
from pathlib import Path
import shutil
import os
from difflib import get_close_matches

logger = logging.getLogger(__name__)

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
    path_obj = Path(filepath)
    
    # Insérer "Archives" entre le dossier parent et le fichier
    archive_path = path_obj.parent / "Archives" / path_obj.name
    
    return archive_path