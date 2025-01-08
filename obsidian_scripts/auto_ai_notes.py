from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import ollama
import os
import time
import re
from sentence_transformers import SentenceTransformer, util

# Configuration
NOTES_DIR = '/mnt/user/Documents/Obsidian/notes'
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

# Fonction pour découper une note en sections
def split_note(content):
    sections = re.split(r'\n{2,}', content)  # Coupe aux doubles sauts de ligne
    return sections

# Génération de tags
def generate_tags(content):
    response = ollama.chat("llama3", f"Quels sont les tags principaux de ce texte : {content}")
    tags = re.findall(r'#(\w+)', response)
    return ', '.join(tags) if tags else "Non classé"

# Résumé de chaque section
def generate_summary(content):
    summary = ollama.chat("llama3", f"Fais-moi un résumé concis de cette section : {content}")
    return summary.strip()

# Fonction pour détecter des notes similaires (backlinks)
def find_similar_notes(section, all_notes):
    similarities = {}
    for note, content in all_notes.items():
        embeddings1 = model.encode(section, convert_to_tensor=True)
        embeddings2 = model.encode(content, convert_to_tensor=True)
        score = util.pytorch_cos_sim(embeddings1, embeddings2).item()
        if score > 0.6:  # Seuil de similarité
            similarities[note] = score
    return similarities

# Gestionnaire d'événements Watchdog
class NoteHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(".md"):
            with open(event.src_path, 'r+', encoding='utf-8') as file:
                content = file.read()
                sections = split_note(content)

                all_notes = {}
                for note in os.listdir(NOTES_DIR):
                    if note.endswith(".md") and note != os.path.basename(event.src_path):
                        with open(os.path.join(NOTES_DIR, note), 'r', encoding='utf-8') as f:
                            all_notes[note] = f.read()

                new_content = ""
                for section in sections:
                    summary = generate_summary(section)
                    tags = generate_tags(section)
                    similar_notes = find_similar_notes(section, all_notes)

                    backlinks = "\n".join([f"- [[{note}]]" for note in similar_notes])

                    new_content += f"""
---
Résumé: {summary}
Tags: {tags}
Liens: 
{backlinks}
---
{section}

"""
                file.seek(0)
                file.write(new_content)
                file.truncate()
                print(f"Note mise à jour : {event.src_path}")

observer = Observer()
observer.schedule(NoteHandler(), path=NOTES_DIR, recursive=True)
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()
