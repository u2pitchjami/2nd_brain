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

  # Emplacement du fichier log
logging.basicConfig(filename='/home/pipo/bin/dev/2nd_brain/obsidian_scripts/logs/auto_tags.log', level=logging.DEBUG, format='%(asctime)s - %(message)s')

def clean_content(content):
    logging.debug(f"[DEBUG] clean_content")
    """
    Nettoie le contenu avant de l'envoyer au modèle.
    - Conserve les blocs de code Markdown (``` ou ~~~).
    - Supprime les balises SVG ou autres éléments non pertinents.
    - Élimine les lignes vides ou répétitives inutiles.
    """
    # Supprimer les balises SVG ou autres formats inutiles
    content = re.sub(r'<svg[^>]*>.*?</svg>', '', content, flags=re.DOTALL)

    # Supprimer les lignes vides multiples
    content = re.sub(r'\n\s*\n', '\n', content)

    return content.strip()

def split_large_note(content, max_words=3000):
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
        blocks = split_large_note(content, max_words=3000)
        print(f"[INFO] La note a été découpée en {len(blocks)} blocs.")

        processed_blocks = []
        for i, block in enumerate(blocks):
            print(f"[INFO] Traitement du bloc {i + 1}/{len(blocks)}...")

            # Étape 2 : Appel au modèle pour reformulation
            prompt = f"""
            You are an intelligent note-organizing assistant. Analyze the following text and identify distinct subjects or topics.
    - **if the content is a bot conversation** :
        - Please identify the main discussion points, decisions, and action items from my conversation below and provide a concise bulleted summary
        - Simplify and reformat the conversation.
        - Extract key ideas and create a structured summary in markdown format.
        - highlights thoughts on topics, good or bad actions in order to draw useful elements or points of vigilance for the future
        - Focus on removing redundant back-and-forth while preserving the core arguments and answers.
    - **If the content is NOT a conversation with ChatGPT**:
        - Rewrite the following text to improve clarity and conciseness. Maintain the original meaning while simplifying complex language, removing unnecessary jargon, and ensuring the content is easily understood by a general audience.
        - The tone should be professional yet approachable.
        - Organize the information logically and use clear, concise sentences
        - For each subject, create a separate section with a clear heading.
        - Organize the content under each heading, reformulating in a clear and simple way but improving the structure and readability and clearly identifying key points.
        - Use markdown formatting for headings and subheadings.
        - Ensure that related information is grouped together logically.
        - Remove unnecessary details or redundancies.
        - Ensure the output is in markdown format.

            Here is the text to simplify:
            {block}
            """
            response = ollama_generate(prompt)
            processed_blocks.append(response.strip())

        # Étape 3 : Fusionner les blocs reformulés
        final_content = "\n\n".join(processed_blocks)

        # Écriture de la note reformulée
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(final_content)
        print(f"[INFO] La note volumineuse a été traitée et enregistrée : {filepath}")

    except Exception as e:
        print(f"[ERREUR] Impossible de traiter {filepath} : {e}")

def is_file_stable(filepath, stability_duration=10):
    """
    Vérifie si un fichier est stable (sa taille ne change plus).
    """
    try:
        logging.debug(f"[DEBUG] test de stabilité {filepath}")
        previous_size = os.path.getsize(filepath)
        time.sleep(stability_duration)
        current_size = os.path.getsize(filepath)
        logging.debug(f"[DEBUG] test de stabilité previous : {previous_size}  current : {current_size}")
        return previous_size == current_size
    except Exception as e:
        print(f"[ERREUR] Impossible de vérifier la stabilité de {filepath} : {e}")
        return False

# Dictionnaire pour suivre les fichiers en traitement
currently_processing = {}

def is_recently_processed(filepath, delay=5):
    """
    Vérifie si un fichier a été récemment modifié par le script lui-même.
    """
    now = time.time()
    if filepath in currently_processing:
        last_processed_time = currently_processing[filepath]
        if now - last_processed_time < delay:
            return True  # Le fichier a été récemment modifié
    # Met à jour le timestamp pour ce fichier
    currently_processing[filepath] = now
    return False


def simplify_note_with_ai(content):
    logging.debug(f"[DEBUG] démarrage du simplify_note_with_ai")
    """
    Reformule et simplifie une note en utilisant Ollama.
    """
    prompt = f"""
    You are an intelligent note-organizing assistant. Analyze the following text and identify distinct subjects or topics.
    - **if the content is a bot conversation** :
        - Please identify the main discussion points, decisions, and action items from my conversation below and provide a concise bulleted summary
        - Simplify and reformat the conversation.
        - Extract key ideas and create a structured summary in markdown format.
        - highlights thoughts on topics, good or bad actions in order to draw useful elements or points of vigilance for the future
        - Focus on removing redundant back-and-forth while preserving the core arguments and answers.
    - **If the content is NOT a conversation with ChatGPT**:
        - Rewrite the following text to improve clarity and conciseness. Maintain the original meaning while simplifying complex language, removing unnecessary jargon, and ensuring the content is easily understood by a general audience.
        - The tone should be professional yet approachable.
        - Organize the information logically and use clear, concise sentences
        - For each subject, create a separate section with a clear heading.
        - Organize the content under each heading, reformulating in a clear and simple way but improving the structure and readability and clearly identifying key points.
        - Use markdown formatting for headings and subheadings.
        - Ensure that related information is grouped together logically.
        - Remove unnecessary details or redundancies.
        - Ensure the output is in markdown format.


    Here is the note:
    {content}
    """

    # Appel à Ollama pour simplifier la note
    response = ollama_generate(prompt)
    print (response)
    return response.strip()

def split_note_by_ai(content):
    logging.debug(f"[DEBUG] Démmarage interrogation Ollama pour Split")
    # Utilisation du prompt que tu as testé
    prompt = f"""
    You are an intelligent note-organizing assistant. Analyze the following text and identify distinct subjects or topics.
    For each subject, create a separate section with a clear heading.
    - Start each section with 'TITLE: <short descriptive title>'.
    - Organize the content under each heading, keeping related information grouped logically.
    - Use markdown formatting for headings and subheadings.
    - Ensure the sections are distinct, well-structured, and concise.

    Here is the text to split:

    
    
    Text to process:
    {content}
    """

    # Appel au modèle IA (ollama)
    response = ollama_generate(prompt)
    print (response)

    # Supprimer l'introduction jusqu'au premier "TITLE:"
    response = re.sub(r'^.*?(?=TITLE:)', '', response, flags=re.DOTALL)

    # Découper les sections basées sur "TITLE:"
    sections = re.split(r'(?=TITLE:)', response)

    # Nettoyer les sections pour éviter les blocs vides
    sections = [s.strip() for s in sections if s.strip()]

    if not sections:
        print(f"[ERREUR] Aucune section détectée avec 'TITLE:' dans la réponse de l'IA.")
        return []

    logging.debug(f"[DEBUG] Sections extraites : {sections}")
    return sections


def create_split_notes(filepath, sections):
    logging.debug(f"[DEBUG] Split : création de fichiers")
    directory = os.path.dirname(filepath)
    created_files = []

    for i, section in enumerate(sections):
        # Extraire le titre d'ollama depuis 'TITLE: ...'
        title_match = re.search(r'TITLE:\s*(.+)', section)
        title = title_match.group(1) if title_match else f"section_{i+1}"
        logging.debug(f"[DEBUG] Split : extraction du titre : {title}")
        
        # Nettoyer le titre pour créer un nom de fichier correct
        safe_title = re.sub(r'[^\w\s-]', '', title)  # Supprimer caractères spéciaux
        safe_title = safe_title[:50].replace(" ", "_").lower()  # Limiter la longueur
        logging.debug(f"[DEBUG] Split : nettoyage du titre : {safe_title}")

        # Créer un nom de fichier
        new_filename = f"{safe_title}.md"
        new_filepath = os.path.join(directory, new_filename)
        logging.debug(f"[DEBUG] Split : création du fichier dans : {new_filepath}")

        # Ajouter les liens pour navigation
        prev_link = f"[[{created_files[-1]}]]" if i > 0 else ""
        next_link = f"[[{safe_title}.md]]" if i < len(sections) - 1 else ""
        logging.debug(f"[DEBUG] Split : création des liens")
        
        # Ajouter YAML + contenu de la section
        yaml_block = [
            "---\n",
            f"title: {title}\n",
            f"created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            "status: processed\n",  # Ajout du status
            "---\n\n",
            f"{prev_link}\n\n",
            section,
            f"\n\n{next_link}"
        ]
        try:
            # Créer et écrire le fichier
            with open(new_filepath, 'w', encoding='utf-8') as new_file:
                new_file.writelines(yaml_block)
                created_files.append(new_filename)
                logging.debug(f"[DEBUG] Split : création du fichier dans : {new_filepath}")
        except Exception as e:
            print(f"[ERREUR] Impossible de créer le fichier {new_filename} : {e}")

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
        "model": "qwen2.5:14b",
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

def should_split_note(content, min_lines=100):
    logging.debug(f"[DEBUG] démarrage should_split_note")
    lines = content.splitlines()
    word_count = len(content.split())
    char_count = len(content)
    logging.debug(f"[DEBUG] should_split_note lines : {len(lines)} words : {word_count} char_count : {char_count}")
    

    return len(lines) >= min_lines

def filter_short_sections(sections, min_word_count=100):
    logging.debug(f"[DEBUG] filter_short_sections")
    """
    Filtre les sections trop courtes et les regroupe avec la section précédente.
    """
    filtered_sections = []
    current_section = ""

    for section in sections:
        # Compter les mots de la section
        word_count = len(section.split())
        if word_count < min_word_count:
            logging.debug(f"[DEBUG] filter_short_sections {word_count} < {min_word_count} --> {section}")
            # Ajouter cette section à la précédente
            current_section += f"\n\n{section}"
        else:
            # Ajouter la section précédente si elle existe
            logging.debug(f"[DEBUG] filter_short_sections else {word_count} < {min_word_count}")
            if current_section.strip():
                filtered_sections.append(current_section.strip())
            # Passer à la nouvelle section
            current_section = section

    # Ajouter la dernière section si elle existe
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

def process_single_note(filepath):
    logging.debug(f"[DEBUG] démarrage du process_single_note pour : {filepath}")
    if not filepath.endswith(".md"):
        return
    try:
        
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
        # Nettoyer le contenu
        cleaned_content = clean_content(content)
        # Vérifier si la note est volumineuse
        word_count = len(cleaned_content.split())
        max_words_for_large_note = 2500  # Définir la limite de mots pour une "grande" note
        logging.debug(f"[DEBUG] process_single_note nombre mots : {word_count}")

        if word_count > max_words_for_large_note:
            print(f"[INFO] La note est volumineuse ({word_count} mots). Utilisation de 'process_large_note'.")
            process_large_note(cleaned_content, filepath)
            return

        # Reformulation normale et vérification de la taille
        simplified_note = simplify_note_with_ai(cleaned_content)
        
        # Étape 2 : Vérification de la taille
        if not should_split_note(simplified_note):
            print(f"[INFO] La note est suffisamment courte, pas de split nécessaire : {filepath}")
            logging.debug(f"[DEBUG] remplacement de la note par la simplification")
            
            
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(simplified_note)
            return
        
        # Étape 3 : Splitter la note si nécessaire
        sections = split_note_by_ai(simplified_note)
        logging.debug(f"[DEBUG] process_single_note : envoie vers split_note_by_ai")
        sections = filter_short_sections(sections, min_word_count=100)
        create_split_notes(filepath, sections)
        logging.debug(f"[DEBUG] process_single_note : envoie vers create_split_notes")
        return

            
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