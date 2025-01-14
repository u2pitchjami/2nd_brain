import os
import re
import requests
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
from datetime import datetime
from prompts import PROMPTS
import time
import logging
import json

# Chemin vers le dossier contenant les notes Obsidian
obsidian_notes_folder = "/mnt/user/Documents/Obsidian/notes"
ollama_api_url = "http://192.168.50.12:11434/api/generate"

  # Emplacement du fichier log
logging.basicConfig(filename='/home/pipo/bin/dev/2nd_brain/obsidian_scripts/logs/auto_tags.log', level=logging.DEBUG, format='%(asctime)s - %(message)s')

def split_by_headings(content):
    """
    Découpe le texte en sections basées sur les titres Markdown (##, ###).
    """
    # Expression régulière pour découper sur ## ou ###
    logging.debug(f"[DEBUG] split_by_headings : lancement fonction")
    sections = re.split(r'\n(?=##|###)', content)
    sections = [s.strip() for s in sections if s.strip()]  # Nettoyer les sections vides
    return sections

# Fonction pour interroger Ollama et générer des tags à partir du contenu d'une note
def get_tags_from_ollama(content):
    logging.debug(f"[DEBUG] tags ollama : lancement fonction")
    prompt = PROMPTS["tags"].format(content=content)
    logging.debug(f"[DEBUG] tags ollama : recherche et lancement du prompt")
    response = ollama_generate(prompt)
    logging.debug(f"[DEBUG] tags ollama : reponse récupéré")
    #print(f"Réponse complète : {response}")
    # EXTRACTION DU JSON VIA REGEX
    match = re.search(r'\{.*?\}', response, re.DOTALL)
    
    if match:
        try:
            tags_data = json.loads(match.group(0))
            tags = tags_data.get("tags", [])
        except json.JSONDecodeError:
            tags = ["Error parsing JSON"]
    else:
        tags = ["No tags found"]

    return tags
            
# Fonction pour générer un résumé automatique avec Ollama
def get_summary_from_ollama(content):
    logging.debug(f"[DEBUG] résumé ollama : lancement fonction")
    prompt = PROMPTS["summary"].format(content=content)
    response = ollama_generate(prompt)
    
    
    logging.debug(f"[DEBUG] summary ollama : reponse récupéré")
   # Nettoyage au cas où Ollama ajoute du texte autour
    match = re.search(r'TEXT START(.*?)TEXT END', response, re.DOTALL)
    if match:
        summary = match.group(1).strip()
    else:
        summary = response  # Si pas de balise trouvée, retourne la réponse complète
    
    # Nettoyage des artefacts
    #summary = clean_summary(summary)
    
    return summary


# Fonction pour ajouter ou mettre à jour les tags, résumés et commandes dans le front matter YAML
def add_metadata_to_yaml(filepath, tags, summary):
    try:    
        with open(filepath, "r", encoding="utf-8") as file:
            lines = file.readlines()
        
        nombre_mots = count_words("".join(lines))
        date_actuelle = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Récupération de la date de création existante ou initialisation
        date_creation = date_actuelle
        yaml_start, yaml_end = -1, -1
        
        for i, line in enumerate(lines):
            if line.strip() == "---":
                if yaml_start == -1:
                    yaml_start = i
                else:
                    yaml_end = i
                    break
            if line.startswith("created:"):
                date_creation = line.split(":")[1].strip()
        logging.debug(f"[DEBUG] Y a t-il une entête ?")
        # Si aucune entête YAML n'existe, la créer
        if yaml_start == -1 or yaml_end == -1:
            missing_summary = not any("summary:" in line for line in lines[yaml_start:yaml_end])
            missing_tags = not any("tags:" in line for line in lines[yaml_start:yaml_end])

            if missing_tags:
                lines.insert(yaml_end, f"tags: [{', '.join(tags)}]\n")
                logging.info(f"Ajout des tags manquants pour {filepath}")

            if missing_summary:
                lines.insert(yaml_end, f"summary: |\n  {summary.replace('\n', '\n  ')}\n")
                logging.info(f"Ajout du résumé manquant pour {filepath}")
                
            yaml_block = [
                "---\n",
                f"tags: [{', '.join(tags)}]\n",
                f"summary: |\n  {summary.replace('\n', '\n  ')}\n",
                f"word_count: {nombre_mots}\n",
                f"created: {date_creation}\n",
                f"last_modified: {date_actuelle}\n",
                "author: \n",
                "status: \n",
                "---\n\n"
            ]
            lines = yaml_block + lines
            logging.info(f"Création d'une entête YAML complète pour {filepath} :\n{''.join(yaml_block)}")
        
        else:
            # Mise à jour des métadonnées existantes
            logging.debug(f"[DEBUG] Il y a déjà une entête")
            inside_yaml = False
            inside_summary = False
            inside_tags = False

            for i in range(yaml_start, yaml_end):
                line = lines[i].strip()

                # Détecte les lignes à traiter
                if line == "---":
                    inside_yaml = not inside_yaml

                if inside_yaml:
                    if line.startswith("tags:"):
                        inside_tags = True
                        lines[i] = f"tags: [{', '.join(tags)}]\n"
                    elif inside_tags and line.startswith("  - "):
                        lines[i] = ""  # Efface les anciennes lignes de tags
                    else:
                        inside_tags = False

                    if line.startswith("summary:"):
                        inside_summary = True
                        lines[i] = f"summary: |\n  {summary.replace('\n', '\n  ')}\n"
                    elif inside_summary and line.startswith("  "):
                        lines[i] = ""  # Efface les anciennes lignes du résumé
                    else:
                        inside_summary = False

                    if line.startswith("word_count:"):
                        lines[i] = f"word_count: {nombre_mots}\n"

                    if line.startswith("last_modified:"):
                        lines[i] = f"last_modified: {date_actuelle}\n"

                       
                        
            # Loguer l'entête après modification
            yaml_block = lines[yaml_start:yaml_end + 1]
            logging.info(f"[YAML MODIFIÉ] pour {filepath} :\n{''.join(yaml_block)}")
            
            missing_summary = not any("summary:" in line for line in lines[yaml_start:yaml_end])
            missing_tags = not any("tags:" in line for line in lines[yaml_start:yaml_end])

            if missing_tags:
                lines.insert(yaml_end, f"tags: [{', '.join(tags)}]\n")
            if missing_summary:
                lines.insert(yaml_end, f"summary: |\n  {summary.replace('\n', '\n  ')}\n")

                
        # Écriture des modifications dans le fichier
        with open(filepath, "w", encoding="utf-8") as file:
            file.writelines(lines)
            logging.info(f"Fichier {filepath} mis à jour avec succès.")
            logging.debug(f"[DEBUG] fichier mis à jour ??? : {line.strip()}")
    
    except Exception as e:
        logging.error(f"Erreur lors de la mise à jour de {filepath} : {e}")
        raise
   

def clean_content(content, filepath):
    logging.debug(f"[DEBUG] clean_content : {filepath}")
    """
    Nettoie le contenu avant de l'envoyer au modèle.
    - Conserve les blocs de code Markdown (``` ou ~~~).
    - Supprime les balises SVG ou autres éléments non pertinents.
    - Élimine les lignes vides ou répétitives inutiles.
    """
    # Supprimer les balises SVG ou autres formats inutiles
    content = re.sub(r'<svg[^>]*>.*?</svg>', '\n', content, flags=re.DOTALL)

    # Supprimer les lignes vides multiples
    #content = re.sub(r'\n\s*\n', '\n', content)

    return content.strip()

def split_large_note(content, max_words=200):
    """
    Découpe une note en blocs de taille optimale (max_words).
    """
    words = content.split()
    blocks = []
    current_block = []

    for word in words:
        current_block.append(word)
        if len(current_block) >= max_words:
            blocks.append(" ".join(current_block))
            current_block = []

    # Ajouter le dernier bloc s'il reste des mots
    if current_block:
        blocks.append(" ".join(current_block))

    return blocks

def process_large_note(content, filepath):
    logging.debug(f"[DEBUG] process_large_note")
    """
    Traite une note volumineuse en la découpant et en envoyant les blocs au modèle.
    """
    try:
        #with open(filepath, 'r', encoding='utf-8') as file:
        #    content = file.read()

        # Étape 1 : Découpage en blocs optimaux
        blocks = split_large_note(content, max_words=200)
        print(f"[INFO] La note a été découpée en {len(blocks)} blocs.")

        processed_blocks = []
        for i, block in enumerate(blocks):
            print(f"[INFO] Traitement du bloc {i + 1}/{len(blocks)}...")

            # Étape 2 : Appel au modèle pour reformulation
            prompt = PROMPTS["split"].format(content=block)
            response = ollama_generate(prompt)
            logging.debug(f"[DEBUG] block {i} : {response}")
            processed_blocks.append(response.strip())

        # Étape 3 : Fusionner les blocs reformulés
        final_content = "\n\n".join(processed_blocks)
        #print ("final content :",final_content)
        # Écriture de la note reformulée
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(final_content)
        print(f"[INFO] La note volumineuse a été traitée et enregistrée : {filepath}")

    except Exception as e:
        print(f"[ERREUR] Impossible de traiter {filepath} : {e}")

def simplify_note_with_ai(content):
    logging.debug(f"[DEBUG] démarrage du simplify_note_with_ai")
    """
    Reformule et simplifie une note en utilisant Ollama.
    """
        
    prompt = PROMPTS["reformulation"].format(content=content)
    # Appel à Ollama pour simplifier la note
    response = ollama_generate(prompt)
    
    return response.strip()

def enforce_titles(response):
    sections = re.split(r'\n(?=##|\n\n)', response)  # Split par titre Markdown ou paragraphes
    processed_sections = []
    for idx, section in enumerate(sections):
        if not section.startswith("TITLE:"):
            title = f"TITLE: Section {idx + 1}"  # Titre par défaut
            section = f"{title}\n{section.strip()}"
        processed_sections.append(section)
    return "\n\n".join(processed_sections)

def split_note_by_ai(content):
    logging.debug(f"[DEBUG] Démmarage interrogation Ollama pour Split")
    # Utilisation du prompt que tu as testé
    #logging.debug(f"[DEBUG] content Split : {content}")
    
    # Vérifie la longueur de la note
    if len(content.split()) < 200:
        logging.debug("[INFO] La note est trop courte pour être divisée.")
        return [content]
    
    prompt = PROMPTS["split"].format(content=content)
    
    # Appel au modèle IA (ollama)
    response = ollama_generate(prompt)
    logging.debug(f"[DEBUG] content Splité : {response}")
    reponse = enforce_titles(response)

    # Supprimer l'introduction jusqu'au premier "TITLE:"
    #response = re.sub(r'^.*?(?=TITLE:)', '', response, flags=re.DOTALL)
    #logging.debug(f"[DEBUG] content Splité suppr intro : {response}")
    
    # Découpe les sections basées sur des titres (par exemple, ## ou ###)
    sections = re.split(r'(?=## )', response)
    logging.debug(f"[DEBUG] Sections après split : {sections}")

    # Filtrer les sections trop courtes
    sections = filter_short_sections(sections, min_word_count=100)
    logging.debug(f"[DEBUG] Sections après filtrage : {sections}")
    if not sections:
        print(f"[ERREUR] Aucune section détectée avec 'TITLE:' dans la réponse de l'IA.")
        return []

    logging.debug(f"[DEBUG] Sections extraites : {sections}")
    return sections


def create_split_notes(filepath, sections):
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


# Traitement pour réponse d'ollama
def ollama_generate(prompt):
    logging.debug(f"[DEBUG] Ollama sollicité")
    payload = {
        "model": "llama3:latest",
        "prompt": prompt
    }
    
    response = requests.post("http://192.168.50.12:11434/api/generate", json=payload, stream=True)
    
    full_response = ""
    for line in response.iter_lines():
        if line:
            try:
                json_line = json.loads(line)
                full_response += json_line.get("response", "")
            except json.JSONDecodeError as e:
                print(f"Erreur de décodage JSON : {e}")
    
    return full_response.strip()

def should_split_note(filepath, content, min_lines=100):
    logging.debug(f"[DEBUG] démarrage should_split_note")
    lines = content.splitlines()
    word_count = len(filepath.split())
    char_count = len(filepath)
    logging.debug(f"[DEBUG] should_split_note file : {filepath} lines : {len(lines)} words : {word_count} char_count : {char_count}")
    

    return len(lines) >= min_lines

def count_words(content):
    logging.debug(f"[DEBUG] def count_word")
    return len(content.split())

def filter_short_sections(sections, min_word_count=100):
    """
    Filtre et fusionne les sections trop courtes.
    """
    logging.debug(f"[DEBUG] entrée filter_short_sections")
    filtered_sections = []
    current_section = ""

    for section in sections:
        word_count = len(section.split())
        if word_count < min_word_count:
            current_section += f"\n\n{section}"  # Ajoute à la section actuelle
            logging.debug(f"[DEBUG] filter_short_sections {word_count} < {min_word_count} --> {section}")
        else:
            if current_section.strip():
                filtered_sections.append(current_section.strip())
                logging.debug(f"[DEBUG] filter_short_sections else {word_count} > {min_word_count}")
            current_section = section  # Nouvelle section

    # Ajouter la dernière section
    if current_section.strip():
        filtered_sections.append(current_section.strip())

    return filtered_sections

class NoteHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not self.is_hidden(event.src_path):
            print(f"[MODIFICATION] {event.src_path}")
            process_single_note(event.src_path)
    
    def on_created(self, event):
        if not self.is_hidden(event.src_path):
            print(f"[CREATION] {event.src_path}")
            process_single_note(event.src_path)
    
    def on_deleted(self, event):
        if not self.is_hidden(event.src_path):
            print(f"[SUPPRESSION] {event.src_path}")
            process_single_note(event.src_path)
    
    def on_moved(self, event):
        if not self.is_hidden(event.src_path) and not self.is_hidden(event.dest_path):
            print(f"[DEPLACEMENT] {event.src_path} -> {event.dest_path}")
            process_single_note(event.dest_path)
    @staticmethod
    def is_hidden(path):
        # Vérifie si le dossier ou fichier est caché (commence par un .)
        return any(part.startswith('.') for part in path.split(os.sep))

def make_properties(content, filepath):
    """
    génère les entêtes.
    """
    logging.debug(f"[DEBUG] Entrée de la fonction make_pro")
    print ("make",filepath)
    tags = get_tags_from_ollama(content)
    summary = get_summary_from_ollama(content)
    add_metadata_to_yaml(filepath, tags, summary)
    logging.debug(f"[DEBUG] process_single_note modif significative")

    # Relecture et comptage après mise à jour complète
    with open(filepath, 'r', encoding='utf-8') as file:
        updated_content = file.read()
    nombre_mots_actuels = count_words(updated_content)
    logging.debug(f"[DEBUG] process_single_note recomptage")

    # Mise à jour du word_count immédiatement
    with open(filepath, "r", encoding="utf-8") as file:
        lines = file.readlines()

    with open(filepath, "w", encoding="utf-8") as file:
        word_count_updated = False
        for i, line in enumerate(lines):
            if line.startswith("word_count:"):
                lines[i] = f"word_count: {nombre_mots_actuels}\n"
                word_count_updated = True
                break
        else:
            # Ajoute word_count s'il n'existe pas
            lines.insert(3, f"word_count: {nombre_mots_actuels}\n")

        file.writelines(lines)

    logging.info(f"Nombre de mots mis à jour pour {filepath}")
    return

def read_note_content(filepath):
    """Lit le contenu d'une note depuis le fichier."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logging.error(f"[ERREUR] Impossible de lire le fichier {filepath} : {e}")
        return None

def split_and_filter_sections(content, min_word_count=100):
    """Découpe le contenu en sections basées sur les titres et filtre les sections courtes."""
    sections = split_by_headings(content)
    logging.debug(f"[DEBUG] Sections extraites : {sections}")
    return filter_short_sections(sections, min_word_count=min_word_count)

def save_sections_as_files(sections, original_filepath):
    """Sauvegarde chaque section dans un nouveau fichier Markdown."""
    base_dir = os.path.dirname(original_filepath)

    for idx, section in enumerate(sections):
        # Extraire le titre ou utiliser un titre par défaut
        title = f"section_{idx + 1}"
        if section.startswith("##") or section.startswith("###"):
            title = section.split("\n")[0].strip("# ").strip()

        # Nettoyage et création du nom de fichier
        filename = f"{title.replace(' ', '_').lower()}.md"
        new_filepath = os.path.join(base_dir, filename)

        # Écriture du fichier
        try:
            with open(new_filepath, 'w', encoding='utf-8') as new_file:
                new_file.write(section)
            logging.info(f"[INFO] Fichier créé : {new_filepath}")
        except Exception as e:
            logging.error(f"[ERREUR] Impossible de créer le fichier {new_filepath} : {e}")


def process_single_note(filepath):
    logging.debug(f"[DEBUG] démarrage du process_single_note pour : {filepath}")
    if not filepath.endswith(".md"):
        return
    try:
        
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Définir le seuil de mots pour déclencher l'analyse
        nombre_mots_actuels = count_words(content)
        seuil_mots_initial = 100
        seuil_modif = 100
        ancienne_valeur = 0
        
        # Lire les métadonnées existantes
        with open(filepath, "r", encoding="utf-8") as file:
            logging.debug(f"[DEBUG] process_single_note lecture des metadonnees")
            lines = file.readlines()
            for line in lines:
                if line.startswith("word_count:"):
                    try:
                        ancienne_valeur = int(line.split(":")[1].strip())
                        logging.debug(f"[DEBUG] process_single_note ligne word_count trouvée")
                    except ValueError:
                        ancienne_valeur = 0  # Si la valeur est absente ou invalide
                                        
                if line.startswith("created:"):
                    logging.debug(f"[DEBUG] process_single_note ligne created trouvée")
                    date_creation = line.split(":")[1].strip()
                    
        print(f"[INFO] Mots avant modif : {ancienne_valeur}, Mots actuels : {nombre_mots_actuels}")
        
        # Conditions d'analyse
        if nombre_mots_actuels < seuil_mots_initial:
            print("[INFO] Note trop courte. Aucun traitement.")
            logging.debug(f"[DEBUG] process_single_note note courte")
            return
        
        # Détection de modification significative
        if nombre_mots_actuels - ancienne_valeur >= seuil_modif or ancienne_valeur == 0:
            print("[INFO] Modification significative détectée. Reformulation du texte.")
            # Nettoyer le contenu
            logging.debug(f"[DEBUG] envoie pour vers clean_content")
            cleaned_content = clean_content(content, filepath)
            # Vérifier si la note est volumineuse
            word_count = len(cleaned_content.split())
            max_words_for_large_note = 3000  # Définir la limite de mots pour une "grande" note
            logging.debug(f"[DEBUG] process_single_note nombre mots : {word_count}")
            if word_count > max_words_for_large_note:
                print(f"[INFO] La note est volumineuse ({word_count} mots). Utilisation de 'process_large_note'.")
                logging.debug(f"[DEBUG] note > 3000 mots")
                content = cleaned_content
                logging.debug(f"[DEBUG] process_single_note : envoie process_large")
                process_large_note(content, filepath)
                logging.debug(f"[DEBUG] process_single_note :retour du process_large")
                if not should_split_note(filepath, content):
                    print(f"[INFO] La note est suffisamment courte, pas de split nécessaire : {filepath}")
                    logging.debug(f"[DEBUG] remplacement de la note par la simplification")
                    make_properties(content, filepath)
                # Étape 3 : Splitter la note si nécessaire
                # Splitter la note directement avec les titres existants (## ou ###)
                #logging.debug(f"[DEBUG] Début du split basé sur les titres")
                
                # Découpe les sections avec les titres Markdown
                #sections = split_by_headings(content)
                #logging.debug(f"[DEBUG] Sections après split_by_headings : {sections}")

                # Filtre les sections trop courtes
                #sections = filter_short_sections(sections, min_word_count=100)
                #logging.debug(f"[DEBUG] Sections après filtre : {sections}")
                #create_split_notes(filepath, sections)
                make_properties(content, filepath)

            else:
                # Nettoyer le contenu
                #cleaned_content = clean_content(content)
                content = cleaned_content
                # Reformulation normale et vérification de la taille
                simplified_note = simplify_note_with_ai(content)
                content = simplified_note
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(content)
                    logging.debug(f"[DEBUG] creation de {filepath}")
                make_properties(content, filepath)
        else:
            print("[INFO] Modification non significative. Pas de mise à jour.")
            logging.debug(f"[DEBUG] process_single_note pas suffisament de modif")   
    except Exception as e:
        print(f"[ERREUR] Impossible de traiter {filepath} : {e}")

# Lancement du watcher pour surveiller les modifications dans le dossier Obsidian
def start_watcher():
    path = obsidian_notes_folder
    observer = PollingObserver()
    observer.schedule(NoteHandler(), path, recursive=True)
    observer.start()
    print(f"Surveillance active sur : {obsidian_notes_folder}")
    logging.debug(f"[DEBUG] démarrage du script : ")

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    start_watcher()