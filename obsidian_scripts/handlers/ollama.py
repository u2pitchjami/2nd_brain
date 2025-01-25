import re
import os
import requests
from handlers.prompts import PROMPTS
import json
import logging

logger = logging.getLogger(__name__)

# Fonction pour interroger Ollama et générer des tags à partir du contenu d'une note
def get_tags_from_ollama(content):
    logging.debug(f"[DEBUG] tags ollama : lancement fonction")
    prompt = PROMPTS["tags"].format(content=content)
    logging.debug(f"[DEBUG] tags ollama : recherche et lancement du prompt")
    response = ollama_generate(prompt)
    logging.debug(f"[DEBUG] tags ollama : réponse récupérée : {response}")

    # EXTRACTION DES TAGS VIA REGEX
    match = re.search(r'\{.*?\}', response, re.DOTALL)  # Tente de capturer un objet JSON complet

    if match:
        try:
            tags_data = json.loads(match.group(0))
            tags = tags_data.get("tags", [])
        except json.JSONDecodeError as e:
            logging.error(f"[ERREUR] Impossible de décoder le JSON complet : {e}")
            tags = ["Error parsing JSON"]
    else:
        # Capture uniquement le tableau
        match = re.search(r'\[.*?\]', response, re.DOTALL)
        if match:
            try:
                tags = json.loads(match.group(0))
            except json.JSONDecodeError as e:
                logging.error(f"[ERREUR] Impossible de décoder le tableau : {e}")
                tags = ["Error parsing JSON"]
        else:
            logging.warning("[WARN] Aucun JSON ou tableau trouvé dans la réponse.")
            tags = ["No tags found"]

    logging.debug(f"[DEBUG] tags ollama : tags extraits : {tags}")
    return tags
            
# Fonction pour générer un résumé automatique avec Ollama
def get_summary_from_ollama(content):
    logging.debug(f"[DEBUG] résumé ollama : lancement fonction")
    prompt = PROMPTS["summary"].format(content=content)
    logging.debug(f"[DEBUG] résumé ollama : recherche et lancement du prompt")
    response = ollama_generate(prompt)
    
    
    logging.debug(f"[DEBUG] summary ollama : reponse récupéré")
   # Nettoyage au cas où Ollama ajoute du texte autour
    match = re.search(r'TEXT START(.*?)TEXT END', response, re.DOTALL)
    logging.debug(f"[DEBUG] summary ollama : Nettoyage au cas où Ollama ajoute du texte autour : {match}")
    if match:
        summary = match.group(1).strip()
        logging.debug(f"[DEBUG] summary ollama : Nettoyage : {summary}")
    else:
        summary = response  # Si pas de balise trouvée, retourne la réponse complète
        logging.debug(f"[DEBUG] summary ollama : Nettoyage : pas de balise trouvée")
    
    # Nettoyage des artefacts
    #summary = clean_summary(summary)
    
    return summary

def simplify_note_with_ai(content):
    logging.debug(f"[DEBUG] démarrage du simplify_note_with_ai")
    """
    Reformule et simplifie une note en utilisant Ollama.
    """
        
    prompt = PROMPTS["reformulation"].format(content=content)
    # Appel à Ollama pour simplifier la note
    logging.debug(f"[DEBUG] simplify_note_with_ai : recherche et lancement du prompt")
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

# Traitement pour réponse d'ollama
def ollama_generate(prompt):
    logging.debug(f"[DEBUG] entrée fonction : ollama_generate")
    ollama_url_generate = os.getenv('OLLAMA_URL_GENERATE')
    model_llama = os.getenv('MODEL_LLAMA')
    
    
    payload = {
        "model": model_llama,
        "prompt": prompt
    }
    
    response = requests.post(ollama_url_generate, json=payload, stream=True)
    
    full_response = ""
    for line in response.iter_lines():
        if line:
            try:
                json_line = json.loads(line)
                full_response += json_line.get("response", "")
            except json.JSONDecodeError as e:
                print(f"Erreur de décodage JSON : {e}")
    
    return full_response.strip()