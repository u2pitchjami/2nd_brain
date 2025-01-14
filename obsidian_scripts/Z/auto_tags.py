import os
import re
import requests
import time
import json
import logging
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
from datetime import datetime

# Chemin vers le dossier contenant les notes Obsidian
obsidian_notes_folder = "/mnt/user/Documents/Obsidian/notes"
ollama_api_url = "http://192.168.50.12:11434/api/generate"

# Configuration basique des logs
logging.basicConfig(
    filename='/home/pipo/bin/dev/2nd_brain/obsidian_scripts/logs/auto_tags.log',  # Emplacement du fichier log
    level=logging.DEBUG,  # Niveau des logs (DEBUG, INFO, WARNING, ERROR)
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Fonction pour interroger Ollama et générer des tags à partir du contenu d'une note
def get_tags_from_ollama(content):
    logging.debug(f"[DEBUG] tags ollama : lancement fonction")
    tag_prompt = f"""
    You are a bot in a read-it-later app and your responsibility is to help with automatic tagging.
    Please analyze the text between the sentences "CONTENT START HERE" and "CONTENT END HERE" and suggest relevant tags that describe its key themes, topics, and main ideas. The rules are:
    - Aim for a variety of tags, including broad categories, specific keywords, and potential sub-genres.
    - The tags language must be in English.
    - If it's a famous website you may also include a tag for the website. If the tag is not generic enough, don't include it.
    - The content can include text for cookie consent and privacy policy, ignore those while tagging.
    - Aim for 3-5 tags.
    - if a specific hardware and/or specific software are use add tags with the names for each.
    - If there are no good tags, leave the array empty.
    
    CONTENT START HERE
    {content[:5000]}
    CONTENT END HERE
    
    Respond in JSON with the key "tags" and the value as an array of string tags.
    """
    
    response = ollama_generate(tag_prompt)
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
    summary_prompt = f"""
    Provide a concise summary of the key points discussed in the following text. Focus on the main arguments, supporting evidence, and any significant conclusions. Present the summary in a bullet-point format, highlighting the most crucial information. Ensure that the summary captures the essence of the text while maintaining clarity and brevity
    Only return the summary itself. Do not add any introduction, explanation, or surrounding text.
    **without including the parts already present** in the "summary:" section. Do not repeat existing elements
    
    TEXT START
    {content[:5000]}
    TEXT END
    """
    response = ollama_generate(summary_prompt)
    
   # Nettoyage au cas où Ollama ajoute du texte autour
    match = re.search(r'TEXT START(.*?)TEXT END', response, re.DOTALL)
    if match:
        summary = match.group(1).strip()
    else:
        summary = response  # Si pas de balise trouvée, retourne la réponse complète
    
    # Nettoyage des artefacts
    summary = clean_summary(summary)
    
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
   

def clean_summary(summary):
    # Supprimer les /t/ ou autres artefacts similaires
    cleaned_summary = re.sub(r'\/t\/', '', summary)
    logging.debug(f"[DEBUG] résumé nettoyé")
    return cleaned_summary



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

def count_words(content):
    logging.debug(f"[DEBUG] def count_word")
    return len(content.split())

# Traitement d'une note individuelle à la volée
def process_single_note(filepath):
    if os.path.isdir(filepath):
        print(f"[INFO] Ignoré : {filepath} est un dossier.")
        return
    try:
        with open(filepath, 'r') as file:
            content = file.read()
            
        # Définir le seuil de mots pour déclencher l'analyse
        nombre_mots_actuels = count_words(content)
        seuil_mots_initial = 50
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
            print("[INFO] Modification significative détectée. Mise à jour des tags et résumé.")
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

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    start_watcher()
