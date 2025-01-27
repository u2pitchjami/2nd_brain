import os
from datetime import datetime
from handlers.ollama import get_summary_from_ollama
from handlers.ollama import get_tags_from_ollama
from handlers.files import count_words
import logging
from handlers.extract_yaml_header import extract_yaml_header
from pathlib import Path

logger = logging.getLogger(__name__)

# Fonction pour ajouter ou mettre à jour les tags, résumés et commandes dans le front matter YAML
def add_metadata_to_yaml(filepath, tags, summary, category, subcategory, status):
    try:    
        logging.debug(f"[DEBUG] add_yaml : démarrage fonction : {filepath} {status}")
        
        
        with open(filepath, "r", encoding="utf-8") as file:
            lines = file.readlines()
        
        
        
        # Initialisation des données
        title = Path(filepath).stem
        source_yaml = ""
        author = ""
        project = ""
        date_creation = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        nombre_mots = count_words("".join(lines))
        if "ChatGPT" in title:
            author = "ChatGPT"
        
        # Recherche des données dans tout le document
        for line in lines:
            if line.startswith("created:"):
                date_creation = line.split(":", 1)[1].strip()
            elif line.startswith("source:"):
                source_yaml = line.split(":", 1)[1].strip()
            elif line.startswith("author:"):
                logging.debug(f"[DEBUG] add_yaml : author trouvé")
                author = line.split(":", 1)[1].strip()
                logging.debug(f"[DEBUG] add_yaml : author {author}")
            elif line.startswith("project:"):
                project = line.split(":", 1)[1].strip()
            elif line.startswith("title:"):
                title = line.split(":", 1)[1].strip()

        # Vérification de l'entête YAML
        yaml_start, yaml_end = -1, -1
        if lines[0].strip() == "---":
            yaml_start = 0
            yaml_end = next((i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---"), -1)

        # Supprimer l'ancienne entête YAML si présente
        if yaml_start != -1 and yaml_end != -1:
            logging.debug(f"[DEBUG] add_yaml : suppression de l'ancienne entête YAML")
            lines = lines[yaml_end + 1:]  # Supprime tout jusqu'à la fin de l'entête YAML

        if not title:
            title = os.path.basename(filepath).replace(".md", "")
        
        # Créer une nouvelle entête YAML complète
        yaml_block = [
            "---\n",
            f"title: {title}\n",
            f"tags: [{', '.join(f'{tag.replace(" ", "_")}' for tag in tags)}]\n",
            f"summary: |\n  {summary.replace('\n', '\n  ')}\n",
            f"word_count: {nombre_mots}\n",
            f"category: {category}\n",
            f"sub category: {subcategory}\n",
            f"created: {date_creation}\n",
            f"last_modified: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"source: {source_yaml}\n",
            f"author: {author}\n",
            f"status: {status}\n",
            f"project: {project}\n",
            "---\n\n"
        ]

        # Insérer la nouvelle entête
        lines = yaml_block + lines
        try:
            logging.debug(f"Add_Metadata_to_yaml : Préparation à écrire dans le filepath : {filepath}")
            # Sauvegarde dans le fichier
            with open(filepath, "w", encoding="utf-8") as file:
                file.writelines(lines)
            logging.info(f"[INFO] Génération de l'entête terminée pour {filepath}")
            logging.debug(f"Add_Metadata_to_yaml Écriture réussie dans le fichier filepath : {filepath}")
        except Exception as e:
            logging.error(f"Add_Metadata_to_yaml Erreur lors de l'écriture dans le fichier filepath : {e}", exc_info=True)   
    except Exception as e:
        logging.error(f"Erreur lors du traitement de l'entête YAML pour {filepath} : {e}")

   
def make_properties(content, filepath, category, subcategory, status):
    """
    Génère les entêtes et met à jour les métadonnées.
    """
    logging.debug(f"[DEBUG] make_pro : Entrée de la fonction pour {filepath}")

    # Extraction de l'entête YAML
    header_lines, content_lines = extract_yaml_header(content)
    content = content_lines

    # Récupération des tags et du résumé
    logging.debug(f"[DEBUG] make_pro : Récupération des tags et résumé pour {filepath}")
    tags = get_tags_from_ollama(content)
    summary = get_summary_from_ollama(content)

    # Mise à jour des métadonnées YAML
    logging.debug(f"[DEBUG] make_pro : Mise à jour du YAML pour {filepath} {status}")
    add_metadata_to_yaml(filepath, tags, summary, category, subcategory, status)

    # Lecture et mise à jour en une seule passe
    with open(filepath, "r+", encoding="utf-8") as file:
        lines = file.readlines()

        # Recalcule du nombre de mots après mise à jour complète
        updated_content = "".join(lines)
        nombre_mots_actuels = count_words(updated_content)
        logging.debug(f"[DEBUG] make_pro : Recalcul du nombre de mots pour {filepath}")

        # Mise à jour de la ligne `word_count`
        word_count_updated = False
        for i, line in enumerate(lines):
            if line.startswith("word_count:"):
                lines[i] = f"word_count: {nombre_mots_actuels}\n"
                word_count_updated = True
                logging.debug(f"[DEBUG] make_pro : Mise à jour de word_count existant pour {filepath}")
                break

        if not word_count_updated:
            # Ajout du champ `word_count` s'il n'existe pas
            logging.debug(f"[DEBUG] make_pro : Ajout du champ word_count pour {filepath}")
            lines.insert(3, f"word_count: {nombre_mots_actuels}\n")

        # Retour au début du fichier et écriture des modifications
        file.seek(0)
        file.writelines(lines)
        file.truncate()  # Supprime tout contenu restant si le nouveau contenu est plus court

    logging.debug(f"[DEBUG] make_pro : Écriture réussie et fichier mis à jour pour {filepath}")


def check_type_header(filepath):
    try:    
        logging.debug(f"[DEBUG] add_yaml : démarrage fonction : {filepath}")
        
        with open(filepath, "r", encoding="utf-8") as file:
            lines = file.readlines()
              
        # Vérification de l'entête YAML
        yaml_start, yaml_end = -1, -1
        if lines[0].strip() == "---":
            yaml_start = 0
            yaml_end = next((i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---"), -1)
            if yaml_end != -1:
                logging.debug(f"[DEBUG] add_yaml : entête YAML détectée ({yaml_start} à {yaml_end})")
                yaml_header = lines[1:yaml_end]
                
                # Récupérer les données existantes
                for line in yaml_header:
                    if line.startswith("type:"):
                        note_type = line.split(":", 1)[1].strip()
                        return note_type
    except Exception as e:
        logging.error(f"Erreur lors du traitement de l'entête YAML pour {filepath} : {e}")           
        
# Fonction pour lire l'entête d'un fichier et récupérer category/subcategory
def extract_category_and_subcategory(filepath):
    """
    Lit l'entête d'un fichier pour extraire la catégorie et la sous-catégorie.
    On suppose que les lignes sont au format :
    category: valeur
    subcategory: valeur
    """
    try:
        with open(filepath, 'r') as file:
            for line in file:
                if line.startswith("category:"):
                    category = line.split(":")[1].strip()
                elif line.startswith("subcategory:"):
                    subcategory = line.split(":")[1].strip()
            return category, subcategory
    except Exception as e:
        logging.error(f"[ERREUR] Impossible de lire l'entête du fichier {file_path} : {e}")
        return None, None                            