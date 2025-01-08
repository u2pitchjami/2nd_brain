import os
import re
import requests
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
from datetime import datetime
import time
import logging
import json

# Chemin vers le dossier contenant les notes Obsidian
obsidian_notes_folder = "/mnt/user/Documents/Obsidian/notes"
ollama_api_url = "http://192.168.50.12:11434/api/generate"

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(message)s')

def split_note_by_ai(content):
    # Utilisation du prompt que tu as testé
    prompt = f"""
    You are an intelligent note-organizing assistant. Analyze the following text and identify distinct subjects or topics.
    For each subject, create a separate section with a clear heading.
    Organize the content under each heading, maintaining the original information but improving structure and readability.
    Use markdown formatting for headings and subheadings.
    Ensure that related information is grouped together logically.
    Split each section in a new .md file and it must contain at least 100 words.
    Each title must be comprehensive and independant, you can take a stuck of the original text title with the title of the section.
    Do not print your intro "I've organized..." and "Here are the distinct..."
    
    
    Text to process:
    {content}
    """

    # Appel au modèle IA (ollama)
    response = ollama_generate(prompt)
    print (response)
    # Découper la réponse en sections basées sur les titres en Markdown
    sections = re.split(r'\n(?=## )', response)  # Découpe à chaque "## Titre"

    return sections

def create_split_notes(filepath, sections):
    base_filename = os.path.splitext(os.path.basename(filepath))[0]
    directory = os.path.dirname(filepath)
    created_files = []

    for i, section in enumerate(sections):
        # Extraire le titre de la section
        title = section.splitlines()[0].replace("##", "").strip()
        
        # Limiter la longueur du titre (max 50 caractères)
        safe_title = title[:50].replace(" ", "_").replace(":", "").lower()
        
        # Si le titre est toujours trop long, on réduit encore et ajoute un identifiant unique
        if len(safe_title) > 50:
            safe_title = safe_title[:50] + f"_{i}"
        
        new_filename = f"{safe_title}.md"
        new_filepath = os.path.join(directory, new_filename)

        # Créer les liens de navigation
        prev_link = f"[[{created_files[-1]}]]" if i > 0 else ""
        next_link = f"[[{sections[i+1].splitlines()[0][:30].replace(' ', '_')}.md]]" if i < len(sections) - 1 else ""

        # Créer le fichier .md avec les liens et le contenu de la section
        yaml_block = [
            "---\n",
            f"title: {title}\n",
            f"created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            "---\n\n",
            f"{prev_link}\n\n",
            section,
            f"\n\n{next_link}"
        ]

        # Écrire le fichier
        with open(new_filepath, 'w', encoding='utf-8') as new_file:
            new_file.writelines(yaml_block)
            created_files.append(new_filename)
            print(f"[NOTE CRÉÉE] {new_filepath}")

    # Supprimer la note d'origine
    #os.remove(filepath)
    #print(f"[SUPPRIMÉE] Note d'origine : {filepath}")



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

def process_single_note(filepath):
    if not filepath.endswith(".md"):
        return
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Étape 1 : Splitter via Ollama
        sections = split_note_by_ai(content)
        
        # Étape 2 : Créer des notes à partir des sections
        create_split_notes(filepath, sections)
    
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