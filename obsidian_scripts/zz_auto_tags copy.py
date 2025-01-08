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
    filename='/home/pipo/bin/obsidian_scripts/logs/auto_tags.log',  # Emplacement du fichier log
    level=logging.INFO,  # Niveau des logs (DEBUG, INFO, WARNING, ERROR)
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Fonction pour interroger Ollama et générer des tags à partir du contenu d'une note
def get_tags_from_ollama(content):
    tag_prompt = f"""
    You are a bot in a read-it-later app and your responsibility is to help with automatic tagging.
    Please analyze the text between the sentences "CONTENT START HERE" and "CONTENT END HERE" and suggest relevant tags that describe its key themes, topics, and main ideas. The rules are:
    - Aim for a variety of tags, including broad categories, specific keywords, and potential sub-genres.
    - The tags language must be in English.
    - If it's a famous website you may also include a tag for the website. If the tag is not generic enough, don't include it.
    - The content can include text for cookie consent and privacy policy, ignore those while tagging.
    - Aim for 3-5 tags.
    - If there are no good tags, leave the array empty.
    
    CONTENT START HERE
    {content[:1000]}
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
    # Extraire les tags après "tags:" ou "Tag:"
    #match = re.search(r'tags[:,]? (.+)', response, re.IGNORECASE)
    #if match:
    #    tags = match.group(1).strip().split(", ")
     #   
    #else:
    #    tags = ["Aucun tag trouvé"]
    
    # Correction ici : pas de lettre par lettre
    #return [tag.strip() for tag in tags if tag.strip()]
        
# Fonction pour générer un résumé automatique avec Ollama
def get_summary_from_ollama(content):
    summary_prompt = f"""
    Provide a concise summary of the key points discussed in the following text. Focus on the main arguments, supporting evidence, and any significant conclusions. Present the summary in a bullet-point format, highlighting the most crucial information. Ensure that the summary captures the essence of the text while maintaining clarity and brevity
    Only return the summary itself. Do not add any introduction, explanation, or surrounding text.

    TEXT START
    {content[:2000]}
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

# Fonction pour extraire les commandes du contenu d'une note
#def extract_commands(content):
#    commands = []
#    explanations = []
#    inside_code_block = False
    
#    for line in content.splitlines():
        # Détection du début de bloc bash
        #if line.strip().startswith("```"):
        #    if inside_code_block:
        #        inside_code_block = False  # Fin de bloc
        #    else:
                # Récupérer le langage après ```
        #        current_language = line.strip()[3:]
        #        if current_language in ["bash", "sh", "python", "sql", "javascript", "go", "powershell"]:
        #            inside_code_block = True
        #    continue  # Saute la ligne avec ```

        # Si on est à l'intérieur d'un bloc code autorisé
       # if inside_code_block:
        #    commands.append(line)
        #    explanation = get_command_explanation(line)
        #    explanations.append(f"{line} - {explanation}")
        #    print(commands)  # Debugging pour voir les commandes extraites

   # return commands, explanations

# Fonction pour obtenir une explication d'une commande via Ollama
def get_command_explanation(command):
    return ollama_generate(f"Explique la commande suivante de manière concise et simple : {command}")

# Fonction pour ajouter ou mettre à jour les tags, résumés et commandes dans le front matter YAML
def add_metadata_to_yaml(filepath, tags, summary):
    try:    
        #if commands is None:
        #   commands = ""
        #if explanations is None:
        #    explanations = ""

        #if commands and len(commands) > 0:
        #    commands = f"```\n{'\n'.join(commands).strip()}\n```"
    #else:
        #   commands = None  # Ne pas insérer de bloc vide

        # Joindre les explications s'il y en a plusieurs
        #if explanations:
        #    explanations = f"```\n{'\n'.join(explanations).strip()}\n```"

        with open(filepath, "r", encoding="utf-8") as file:
            lines = file.readlines()
        
        nombre_mots = count_words("".join(lines))
        date_actuelle = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Récupération de la date de création existante ou initialisation
        date_creation = date_actuelle
        for line in lines:
            if line.startswith("created:"):
                date_creation = line.split(":")[1].strip()
                break
        
        
        # Vérifier s'il y a déjà des métadonnées
        if lines[0].strip() != "---":
            lines.insert(0, "---\n")
            lines.insert(1, f"tags: [{', '.join(tags)}]\n")
            lines.insert(2, f"summary: |\n  {summary.replace('\n', '\n  ')}\n")
            lines.insert(3, f"word_count: {nombre_mots}\n")
            lines.insert(4, f"created: {date_creation}\n")
            lines.insert(5, f"last_modified: {date_actuelle}\n")
            lines.insert(6, "author: \n")
            lines.insert(7, "status: \n")
            lines.insert(8, "---\n\n")
            logging.info(f"Création de l'entête YAML pour {filepath}")
            # ✅ N'ajouter commands/explanations que si non vide
            #if commands:
            #    lines.insert(3, f"commands: {commands}\n")
            #if explanations:
            #    lines.insert(4, f"explanations: {explanations}\n")
            
        
        else:
            # Mise à jour des métadonnées existantes
            summary_updated = False
            for i, line in enumerate(lines):
                if line.strip().startswith("tags:"):
                    lines[i] = f"tags: [{', '.join(tags)}]\n"
                    logging.info(f"Mise à jour des tags pour {filepath}")
                if line.strip().startswith("summary:"):
                    lines[i] = f"summary: |\n  {summary.replace('\n', '\n  ')}\n"
                    summary_updated = True
                    logging.info(f"Mise à jour du résumé pour {filepath}")
                if line.strip().startswith("word_count:"):
                    lines[i] = f"word_count: {nombre_mots}\n"
                if line.strip().startswith("last_modified:"):
                    lines[i] = f"last_modified: {date_actuelle}\n"
                if line.strip().startswith("created:") and "created" not in locals():
                    date_creation = line.split(":")[1].strip()
                
                # ✅ Met à jour uniquement si non vide
                #if line.strip().startswith("commands:") and commands:
                #    lines[i] = f"commands: {commands}\n"
                #if line.strip().startswith("explanations:") and explanations:
            #     lines[i] = f"explanations: {explanations}\n"

            # Ajouter summary s'il n'existe pas encore
            if not summary_updated:
                lines.insert(2, f"summary: |\n  {summary.replace('\n', '\n  ')}\n")
                logging.info(f"Ajout du résumé manquant pour {filepath}")
        with open(filepath, "w", encoding="utf-8") as file:
            file.writelines(lines)
            logging.info(f"Fichier {filepath} mis à jour avec succès.")
    except Exception as e:
        logging.error(f"Erreur lors de la mise à jour de {filepath} : {e}")
        raise  # Laisse l'exception remonter après l'avoir loguée

def clean_summary(summary):
    # Supprimer les /t/ ou autres artefacts similaires
    cleaned_summary = re.sub(r'\/t\/', '', summary)
    return cleaned_summary

# Classe pour surveiller les modifications des notes et appliquer automatiquement les mises à jour
#class NoteHandler(FileSystemEventHandler):
#    def on_modified(self, event):
#        if event.src_path.endswith(".md"):
#            print(f"Modification détectée : {event.src_path}")
#            process_single_note(event.src_path)


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
            lines = file.readlines()
            for line in lines:
                if line.startswith("word_count:"):
                    ancienne_valeur = int(line.split(":")[1].strip())
                if line.startswith("created:"):
                    date_creation = line.split(":")[1].strip()
                    
        print(f"[INFO] Mots avant modif : {ancienne_valeur}, Mots actuels : {nombre_mots_actuels}")

        # Conditions d'analyse
        if nombre_mots_actuels < seuil_mots_initial:
            print("[INFO] Note trop courte. Aucun traitement.")
            return

        if nombre_mots_actuels - ancienne_valeur >= seuil_modif or ancienne_valeur == 0:
            print("[INFO] Modification significative détectée. Mise à jour des tags et résumé.")
            tags = get_tags_from_ollama(content)
            summary = get_summary_from_ollama(content)
            add_metadata_to_yaml(filepath, tags, summary)
        else:
            print("[INFO] Modification non significative. Pas de mise à jour.")
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
