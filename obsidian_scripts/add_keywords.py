import yaml

# Charger le fichier YAML
def load_yaml(file_path):
    """Charge les tags et mots-clés depuis le fichier YAML."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}  # Si le fichier est vide, retourne un dictionnaire vide
    except FileNotFoundError:
        return {}  # Si le fichier n'existe pas, retourne un dictionnaire vide
    except Exception as e:
        print(f"Erreur lors du chargement du fichier YAML : {e}")
        raise

# Sauvegarder le fichier YAML
def save_yaml(file_path, data):
    """Sauvegarde les tags et mots-clés dans le fichier YAML."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        print(f"Fichier mis à jour : {file_path}")
    except Exception as e:
        print(f"Erreur lors de l'enregistrement du fichier YAML : {e}")
        raise

# Ajouter ou modifier un tag
def add_or_update_tag(file_path, tag, keywords):
    """Ajoute ou met à jour un tag et ses mots-clés."""
    data = load_yaml(file_path)

    # Vérifie si le tag existe
    if tag in data:
        print(f"Le tag '{tag}' existe déjà. Les mots-clés seront fusionnés.")
        # Fusionne les mots-clés existants avec les nouveaux
        existing_keywords = set(data[tag].split(", "))
        new_keywords = set(keywords)
        data[tag] = ", ".join(sorted(existing_keywords.union(new_keywords)))
    else:
        # Ajoute un nouveau tag
        data[tag] = ", ".join(sorted(keywords))

    save_yaml(file_path, data)
    print(f"Le tag '{tag}' a été mis à jour avec les mots-clés : {', '.join(keywords)}")

# Supprimer un tag
def delete_tag(file_path, tag):
    """Supprime un tag du fichier YAML."""
    data = load_yaml(file_path)
    if tag in data:
        del data[tag]
        save_yaml(file_path, data)
        print(f"Le tag '{tag}' a été supprimé.")
    else:
        print(f"Le tag '{tag}' n'existe pas.")

# Interface utilisateur pour gérer les tags
def main():
    file_path = "/home/pipo/bin/dev/2nd_brain/obsidian_scripts/handlers/keywords.yaml"  # Chemin vers le fichier YAML
    print("=== Gestion des Tags ===")
    while True:
        print("\nOptions :")
        print("1. Ajouter ou modifier un tag")
        print("2. Supprimer un tag")
        print("3. Quitter")
        choice = input("Entrez votre choix : ").strip()

        if choice == "1":
            tag = input("Entrez le tag à ajouter ou modifier : ").strip()
            keywords = input("Entrez les mots-clés associés, séparés par des virgules : ").strip().split(",")
            keywords = [keyword.strip() for keyword in keywords]  # Nettoie les espaces
            add_or_update_tag(file_path, tag, keywords)

        elif choice == "2":
            tag = input("Entrez le tag à supprimer : ").strip()
            delete_tag(file_path, tag)

        elif choice == "3":
            print("Au revoir !")
            break

        else:
            print("Choix invalide. Veuillez réessayer.")

if __name__ == "__main__":
    main()