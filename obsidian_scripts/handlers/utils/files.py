import os
import re
import shutil
from datetime import datetime
import logging
import fnmatch
from pathlib import Path
import time
from handlers.process.prompts import PROMPTS
from handlers.utils.process_note_paths import get_path_from_classification, load_note_paths
from handlers.utils.process_note_paths import is_folder_included
from handlers.process.ollama import ollama_generate
import fnmatch
import unicodedata

logger = logging.getLogger()

def copy_file_with_date(filepath, destination_folder):
    """
    Copie un fichier en ajoutant la date au nom.
    """
    try:
        # Obtenir le nom de base du fichier
        filename = os.path.basename(filepath)
        
        # Extraire le nom et l'extension du fichier
        name, ext = os.path.splitext(filename)
        
        # Obtenir la date actuelle au format souhaité
        date_str = datetime.now().strftime("%y%m%d")  # Exemple : '250112'
        
        # Construire le nouveau nom avec la date
        new_filename = f"{date_str}_{name}{ext}"
        
        # Construire le chemin complet de destination
        destination_path = os.path.join(destination_folder, new_filename)
        
        # Déplacer le fichier
        shutil.copy(filepath, destination_path)
        
        print(f"Fichier copié avec succès : {destination_path}")
    except Exception as e:
        print(f"Erreur lors de la copie du fichier : {e}")
        
def move_file_with_date(filepath, destination_folder):
    """
    déplace un fichier en ajoutant la date au nom.
    """
    try:
        # Obtenir le nom de base du fichier
        filename = os.path.basename(filepath)
        
        # Extraire le nom et l'extension du fichier
        name, ext = os.path.splitext(filename)
        
        # Obtenir la date actuelle au format souhaité
        date_str = datetime.now().strftime("%y%m%d")  # Exemple : '250112'
        
        # Construire le nouveau nom avec la date
        new_filename = f"{date_str}_{name}{ext}"
        
        # Construire le chemin complet de destination
        destination_path = os.path.join(destination_folder, new_filename)
        
        # Déplacer le fichier
        shutil.move(filepath, destination_path)
        
        print(f"Fichier déplacé avec succès : {destination_path}")
    except Exception as e:
        print(f"Erreur lors du déplacement du fichier : {e}")
        
    
def copy_to_archives(filepath):
    """
    Mouvemente le fichier vers le dossier Archives de sa catégorie.
    """
    try:
        # Convertir en objet Path
        file_path_obj = Path(filepath)
        
        archives_dir = file_path_obj.parent / "Archives"  # Ajouter "Archives" au dossier parent
        archives_dir.mkdir(parents=True, exist_ok=True)  # Créer le dossier Archives s'il n'existe pas
        new_path = archives_dir / file_path_obj.name  # Conserve le même nom de fichier dans Archives
        logging.debug(f"[DEBUG] copy_to_archive : construction de : {archives_dir}")
    except ValueError:
        logging.error(f"Impossible de modifier le nom du fichier : {filepath}")
        return None
    try:
        shutil.copy(filepath, archives_dir)
        logging.info(f"[INFO] copy réussi vers : {new_path}")
        return new_path
    except ValueError:
        logging.error(f"Impossible de copier le fichier vers : {archives_dir}")
        return None

### NON UTILISE    
def generate_unique_filename_from_folder(filepath, base_folder):
    """
    Génère un nom de fichier unique basé sur le contenu et vérifie dans un dossier cible.
    """
    logging.debug(f"[DEBUG] generate_unique_filename_from_folder")
    content = read_note_content(filepath)
    # Prompt pour Ollama
    prompt = PROMPTS["make_file_name"].format(content=content)
    logging.debug(f"[DEBUG] generate_unique_filename_from_folder : {prompt}")

    logging.debug(f"[DEBUG] generate_unique_filename_from_folder : envoie vers ollama") 
    # Appel à Ollama
    base_filename = ollama_generate(prompt).strip().replace(" ", "_").lower()
    logging.debug(f"[DEBUG] generate_unique_filename_from_folder : reponse {base_filename}")
     # Vérifie l'extension
    if not base_filename.endswith(".md"):
        base_filename += ".md"
    
    # Vérifie les doublons dans le dossier
    target_folder = Path(base_folder)
    filename = base_filename
    counter = 1
    while (target_folder / f"{filename}").exists():
        filename = f"{base_filename}_{counter}"
        counter += 1

    return f"{filename}"

def rename_file(filepath):
    """
    Renomme un fichier avec un nouveau nom tout en conservant son dossier d'origine.
    """
    logging.debug(f"[DEBUG] entrée rename_file")
    try:
        file_path = Path(filepath)
        # Obtenir la date actuelle au format souhaité
        if not file_path.exists():
            logging.error(f"[ERREUR] Le fichier {filepath} n'existe pas.")
            raise # Ou lève une exception si c'est critique
        logging.debug(f"[DEBUG] rename_file file_path.name {file_path.name}")
        date_str = datetime.now().strftime("%y%m%d")  # Exemple : '250112'
        new_name = f"{date_str}_{sanitize_filename(file_path.name)}"
        new_path = file_path.parent / new_name  # Nouveau chemin dans le même dossier
        
               
        # Résolution des collisions : ajouter un suffixe si le fichier existe déjà
        counter = 1
        while new_path.exists():
            new_name = f"{date_str}_{sanitize_filename(file_path.stem)}_{counter}{file_path.suffix}"
            new_path = file_path.parent / new_name
            counter += 1
        
        
        file_path.rename(new_path)  # Renomme le fichier
        logging.info(f"[INFO] Note renommée : {filepath} --> {new_path}")
        return new_path
    except Exception as e:
            logging.error(f"[ERREUR] Anomalie lors du renommage : {e}")
            raise

def sanitize_filename(filename):
    # Remplace les caractères interdits par des underscores
    try:
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)  # Pour Windows
        sanitized = sanitized.replace(' ', '_')  # Remplace les espaces par des underscores
        return sanitized
    except Exception as e:
            logging.error(f"[ERREUR] Anomalie lors du sanitized : {e}")
            return

def make_relative_link(original_path, link_text="Voir la note originale"):
    """
    Convertit un chemin absolu en lien Markdown relatif.
    
    :param original_path: Chemin absolu du fichier cible
    :param base_path: Répertoire de base pour générer des liens relatifs
    :param link_text: Texte visible pour le lien (par défaut : "Voir la note originale")
    :return: Lien Markdown au format [texte](chemin_relatif)
    """
    base_path = os.getenv('BASE_PATH')
    
    
    original_path = Path(original_path)
    base_path = Path(base_path).resolve()
    
     # Vérifie que le fichier appartient au répertoire de base
    if base_path in original_path.parents:
        # Extraire le chemin relatif
        relative_path = original_path.relative_to(base_path)
        return f"[{link_text}]({relative_path})"
    else:
        raise ValueError(f"Le fichier {original_path} est hors du répertoire de base {base_path}")
    
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
    
from pathlib import Path
import time

def get_recently_modified_files(base_dirs, time_threshold_seconds):
    """
    Parcourt les dossiers `storage` et retourne les fichiers Markdown modifiés récemment.

    :param base_dirs: Liste des dossiers à scanner.
    :param time_threshold_seconds: Temps en secondes (ex: 3600 pour 1h).
    :return: Liste des chemins de fichiers Markdown modifiés récemment.
    """
    note_paths = load_note_paths()
    current_time = time.time()
    recent_files = []

    # 1️⃣ Charger une seule fois tous les dossiers `storage`
    storage_folders = {
        folder_info["path"]
        for folder_info in note_paths["folders"].values()
        if folder_info.get("folder_type") == "storage"
    }

    logging.debug(f"[DEBUG] Dossiers 'storage' chargés : {len(storage_folders)}")

    # 2️⃣ Parcourir uniquement les dossiers `storage`
    for base_dir in base_dirs:
        base_path = Path(base_dir)
        if not base_path.exists():
            logging.warning(f"[ATTENTION] Le dossier {base_dir} n'existe pas.")
            continue

        for folder in storage_folders:
            folder_path = Path(folder)
            if not folder_path.exists():
                continue  # Ignorer les dossiers supprimés

            # 3️⃣ Rechercher uniquement les fichiers Markdown dans ces dossiers
            for file in folder_path.glob("*.md"):  # 🔹 Pas de rglob, + rapide
                if file.is_file() and not file.name.startswith('.'):  # 🔹 Ignore fichiers cachés
                    # Vérifier la date de modification
                    last_modified = file.stat().st_mtime
                    if current_time - last_modified <= time_threshold_seconds:
                        logging.info(f"[INFO] Fichier modifié récemment : {file}")
                        recent_files.append(file)

    logging.debug(f"[DEBUG] Total fichiers récents trouvés : {len(recent_files)}")
    return recent_files


def load_excluded_patterns(file_path):
    """
    Charge les patterns globaux à exclure depuis un fichier texte.

    :param file_path: Chemin du fichier texte contenant les exclusions.
    :return: Liste des patterns globaux.
    """
    excluded_patterns = []
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            excluded_patterns = [line.strip() for line in file if line.strip()]
            logging.debug(f"[DEBUG] CONTENU DU FICHIER {excluded_patterns}")
    except FileNotFoundError:
        print(f"[ATTENTION] Le fichier {file_path} n'existe pas. Aucune exclusion appliquée.")
    return excluded_patterns

def is_in_excluded_folder(path):
    """
    Vérifie si un chemin se trouve dans un dossier exclu en utilisant pathlib.
    """
    exclude_file = os.getenv('EXCLUDE_FILE')
    exclude_file = load_excluded_patterns(exclude_file)
    logging.debug("[DEBUG] fichier exclusion : %s",exclude_file)
    # exclude_file doit être une liste de motifs, pas un chemin de fichier
    excluded_dirs = [pattern.strip("/*") for pattern in exclude_file]  # Nettoyage des motifs
    path_parts = Path(path).parts  # Décompose le chemin en parties

    logging.debug(f"[DEBUG] Chemin à vérifier : {path}")
    logging.debug(f"[DEBUG] Motifs exclus : {excluded_dirs}")
    logging.debug(f"[DEBUG] Parties du chemin : {path_parts}")

    # Vérifie si une des parties du chemin correspond à un dossier exclu
    return any(excluded in path_parts for excluded in excluded_dirs)
