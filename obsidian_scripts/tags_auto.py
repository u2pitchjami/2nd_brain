import os
import requests

obsidian_notes_folder = "/chemin/vers/tes/notes"
ollama_api_url = "http://localhost:11434/api/generate"

def get_tags_from_ollama(content):
    payload = {
        "model": "llama3",
        "prompt": f"Analyse le texte suivant et génère des tags pertinents : {content}"
    }
    response = requests.post(ollama_api_url, json=payload, stream=True)
    # Reconstituer la réponse complète
    full_response = ""
    for line in response.iter_lines():
        if line:
            try:
                json_line = json.loads(line)
                full_response += json_line.get("response", "")
            except json.JSONDecodeError as e:
                print(f"Erreur de décodage JSON : {e}")
    
    print("Réponse complète :")
    print(full_response)
    return full_response.strip().split(", ")
    
    
    tags = response.json().get("response", "").strip().split(", ")
    return tags

def tag_notes():
    for filename in os.listdir(obsidian_notes_folder):
        if filename.endswith(".md"):
            filepath = os.path.join(obsidian_notes_folder, filename)
            with open(filepath, 'r') as file:
                content = file.read()
            
            tags = get_tags_from_ollama(content)
            with open(filepath, 'a') as file:
                file.write(f"\n\n#tags: {', '.join(tags)}")

            print(f"{filename} - Tags ajoutés : {tags}")

tag_notes()