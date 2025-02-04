import yaml
import time
import json
from pathlib import Path
import os

def extract_yaml_tags(note_file):
    """
    Extrait les tags depuis l'entête YAML de la note.
    """
    try:
        with open(note_file, 'r', encoding='utf-8') as file:
            content = file.read()
            if content.startswith('---'):
                yaml_part = content.split('---')[1]
                yaml_data = yaml.safe_load(yaml_part)
                tags = yaml_data.get('tags', [])

                # Cas 1 : Liste YAML (tags sous forme de liste)
                if isinstance(tags, list):
                    return tags

                # Cas 2 : Liste JSON (tags sous forme de chaîne)
                if isinstance(tags, str):
                    # Tentative de parsing si c'est une chaîne JSON
                    try:
                        parsed_tags = json.loads(tags)
                        if isinstance(parsed_tags, list):
                            return parsed_tags
                    except json.JSONDecodeError:
                        # Si ce n'est pas du JSON, on considère que c'est une chaîne simple
                        return [tags.strip()]

        return []  # Pas de tags trouvés
    except Exception as e:
        print(f"[ERREUR] Impossible de lire les tags YAML de {note_file}: {e}")
        return []


def is_hidden(filepath):
    return any(part.startswith('.') for part in filepath.parts)

def is_in_technical_folder(filepath):
    return 'Z_technical' in filepath.parts

def extract_yaml_status(note_file):
    """
    Extrait le status depuis l'entête YAML de la note.
    """
    try:
        with open(note_file, 'r', encoding='utf-8') as file:
            content = file.read()
            if content.startswith('---'):
                yaml_part = content.split('---')[1]
                yaml_data = yaml.safe_load(yaml_part)
                return yaml_data.get('status', 'active')  # Par défaut à 'active' si non trouvé
    except Exception as e:
        print(f"[ERREUR] Impossible de lire l'entête YAML de {note_file}: {e}")
    return 'active'  # Valeur par défaut si l'entête YAML est manquante ou mal formée

def restructure_note_paths(old_note_paths_path='note_paths.json', new_structure_path='structured_note_paths.json'):
    with open(old_note_paths_path, 'r', encoding='utf-8') as file:
        old_data = json.load(file)
    
    structured_data = {
        "notes": [],
        "categories": [],
        "folders": []
    }

    folder_id = 1
    category_id = 1
    note_id = 1

    for key, details in old_data.items():
        category_entry = {
            "id": category_id,
            "category": details.get("category", ""),
            "subcategory": details.get("subcategory", ""),
            "description": details.get("explanation", "")
        }
        structured_data["categories"].append(category_entry)

        folder_entry = {
            "id": folder_id,
            "path": details["path"],
            "folder_type": details.get("folder_type", "storage")
        }
        structured_data["folders"].append(folder_entry)

        note_files = Path(details["path"]).glob("*.md")
        for note_file in note_files:
            if is_hidden(note_file) or is_in_technical_folder(note_file):
                continue
            
            note_title = note_file.stem.replace("_", " ")
            
            # Récupérer le status depuis l'entête YAML
            note_status = extract_yaml_status(note_file)
            
            # Obtenir les dates réelles du fichier
            stat = os.stat(note_file)
            created_at = stat.st_ctime
            modified_at = stat.st_mtime
            note_tags = extract_yaml_tags(note_file)

            note_entry = {
                "id": note_id,
                "title": note_title,
                "file_name": note_file.name,
                "path_id": folder_id,
                "category_id": category_id,
                "created_at": time.strftime('%Y-%m-%d', time.localtime(created_at)),
                "modified_at": time.strftime('%Y-%m-%d', time.localtime(modified_at)),
                "tags": note_tags,
                "status": note_status
            }
            structured_data["notes"].append(note_entry)
            note_id += 1

        folder_id += 1
        category_id += 1

    with open(new_structure_path, 'w', encoding='utf-8') as file:
        json.dump(structured_data, file, indent=4)

    print(f"[INFO] Conversion terminée. Nouveau fichier : {new_structure_path}")


if __name__ == "__main__":
    restructure_note_paths(old_note_paths_path='note_paths.json', new_structure_path='structured_note_paths.json')
