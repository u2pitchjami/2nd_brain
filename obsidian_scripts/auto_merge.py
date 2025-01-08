import os
import re
import requests
import time
import json
import logging
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
from datetime import datetime
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

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

def split_note_by_ai(content):
    # Prompt pour Ollama
    logging.debug(f"[DEBUG] lancement split")
    prompt = f"""
    You are an intelligent note-organizing assistant. Analyze the following text and identify distinct subjects or topics.
    For each subject, create a separate section with a clear heading.
    Organize the content under each heading, maintaining the original information but improving structure and readability.
    Use markdown formatting for headings and subheadings.
    Ensure that related information is grouped together logically
    Split each section in a new .md file with a link with the previous note and the next note
    
    TEXT START
    {content[:5000]}
    TEXT END
    
    """
    
    # Appel à Ollama pour générer les sections
    response = ollama_generate(prompt)
    print (response)
    try:
        sections = json.loads(response)
    except json.JSONDecodeError:
        sections = {"Note principale": content}  # Si l'IA échoue, garder la note complète

    return sections

# Fonction pour ajouter ou mettre à jour les tags, résumés et commandes dans le front matter YAML
def add_metadata_to_yaml(filepath, tags, summary, sections):
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
        
        # Étape 1 : Découpage basé sur l'IA
        sections = split_note_by_ai(content)
        
        base_filename = os.path.splitext(os.path.basename(filepath))[0]
        directory = os.path.dirname(filepath)
        created_files = []
        logging.debug(f"[DEBUG] Étape 1 : Découpage basé sur l'IA")

        # Étape 2 : Créer une note pour chaque section identifiée
        for title, section in sections.items():
            safe_title = title.replace(" ", "_").replace(":", "").lower()
            new_filename = f"{base_filename}_{safe_title}.md"
            new_filepath = os.path.join(directory, new_filename)
            logging.debug(f"[DEBUG] Étape 2 : Créer une note pour chaque section identifiée")
        
            # Générer tags et résumé
            section_tags = get_tags_from_ollama(section)
            section_summary = get_summary_from_ollama(section)
            
            with open(new_filepath, 'w', encoding='utf-8') as new_file:
                yaml_block = [
                    "---\n",
                    f"title: {title}\n",
                    f"tags: [{', '.join(section_tags)}]\n",
                    f"summary: |\n  {section_summary.replace('\n', '\n  ')}\n",
                    f"created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
                    "---\n\n",
                    section
                ]
                new_file.writelines(yaml_block)
                created_files.append(new_filename)
                logging.info(f"Création de {new_filepath}")
        
        # Étape 3 : Supprimer la note originale après découpage
        os.remove(filepath)
        logging.info(f"Note originale supprimée : {filepath}")

    except Exception as e:
        logging.error(f"Erreur lors du traitement de {filepath} : {e}")

#découpage de sections
def split_note(content):
    logging.debug(f"[DEBUG] démarrage Split : ")
    sections = re.split(r'\n{2,}', content)  # Coupe aux doubles sauts de ligne
    return sections

#backlink
def find_similar_notes(section, all_notes):
    logging.debug(f"[DEBUG] démarrage Backlink : ")
    similarities = {}
    for note, content in all_notes.items():
        embeddings1 = model.encode(section, convert_to_tensor=True)
        embeddings2 = model.encode(content, convert_to_tensor=True)
        score = util.pytorch_cos_sim(embeddings1, embeddings2).item()
        if score > 0.6:  # Seuil de similarité
            similarities[note] = score
    return similarities


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
