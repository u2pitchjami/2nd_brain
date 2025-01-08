import os
import re
import requests
import time
import json
from watchdog.observers.polling import PollingObserver

from watchdog.events import FileSystemEventHandler

# Chemin vers le dossier contenant les notes Obsidian
obsidian_notes_folder = "/mnt/user/Documents/Obsidian/notes/Clippings"
ollama_api_url = "http://192.168.50.12:11434/api/generate"

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
    Summarize the following text clearly and concisely. 
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
    
    with open(filepath, "r", encoding="utf-8") as file:
        lines = file.readlines()

    # Vérifier s'il y a déjà des métadonnées
    if lines[0].strip() != "---":
        lines.insert(0, "---\n")
        lines.insert(1, f"tags: [{', '.join(tags)}]\n")
        lines.insert(2, f"summary:|  {summary}\n")
        lines.insert(5, "---\n\n")
    
    else:
        summary_updated = False
        for i, line in enumerate(lines):
            if line.strip().startswith("tags:"):
                lines[i] = f"tags: [{', '.join(tags)}]\n"
            if line.strip().startswith("summary:"):
                lines[i] = f"summary:|  {summary}\n"
                summary_updated = True
            
        # Ajouter summary s'il n'existe pas encore
        if not summary_updated:
            lines.insert(2, f"summary:|  {summary}\n")

    with open(filepath, "w", encoding="utf-8") as file:
        file.writelines(lines)


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
        print(f"[MODIFICATION] {event.src_path}")
        process_single_note(event.src_path)
    def on_created(self, event):
        print(f"[CREATION] {event.src_path}")
        process_single_note(event.src_path)
    def on_deleted(self, event):
        print(f"[SUPPRESSION] {event.src_path}")
        process_single_note(event.src_path)
    def on_moved(self, event):
        print(f"[DEPLACEMENT] {event.src_path} -> {event.dest_path}")
        process_single_note(event.src_path) 
        
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


# Traitement d'une note individuelle à la volée
def process_single_note(filepath):
    with open(filepath, 'r') as file:
        content = file.read()
    # Si le fichier contient déjà des tags ou un résumé, on ne fait rien
    if "tags:" in content and "summary:" in content:
        print(f"Le fichier {filepath} a déjà été analysé.")
        return
    tags = get_tags_from_ollama(content)
    summary = get_summary_from_ollama(content)
    #commands, explanations = extract_commands(content)
    #add_metadata_to_yaml(filepath, tags, summary, commands, explanations)
    add_metadata_to_yaml(filepath, tags, summary)
    print(f"{filepath} - Mise à jour des métadonnées effectuée.")

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
