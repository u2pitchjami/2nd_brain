def verify_and_correct_category(filepath):
    """
    Vérifie que la catégorie et la sous-catégorie d'un fichier correspondent à son emplacement.
    Si ce n'est pas le cas, corrige le fichier ou le déplace.
    """
    try:
        # Extraire catégorie et sous-catégorie de l'entête
        category, subcategory = extract_category_and_subcategory(filepath)
        if not category or not subcategory:
            logging.warning(f"[ATTENTION] Impossible d'extraire catégorie/subcatégorie pour {filepath}")
            return False

        # Trouver le chemin cible
        expected_path = get_path_from_classification(category, subcategory, NOTE_PATHS)
        if not expected_path or not expected_path.exists():
            logging.warning(f"[ATTENTION] Aucun chemin défini ou introuvable pour {category}/{subcategory}")
            return False

        # Vérifier si le fichier est déjà dans le bon dossier
        current_path = filepath.parent.resolve()
        if current_path != expected_path.resolve():
            # Récupération de l'archive
            archive_path = add_archives_to_path(filepath)
            if not archive_path or not archive_path.exists():
                logging.warning(f"[ATTENTION] Aucun fichier archive trouvé")
                return False

            # Modification catégorie dans l'archive
            with open(archive_path, "r+", encoding="utf-8") as file:
                lines = file.readlines()
                for i, line in enumerate(lines):
                    if line.startswith("category:"):
                        lines[i] = f"category: {category}\n"
                    elif line.startswith("sub category:"):
                        lines[i] = f"sub category: {subcategory}\n"
                file.seek(0)
                file.writelines(lines)
                file.truncate()

            # Déplacer le fichier au bon endroit
            new_path = expected_path / archive_path.name
            archive_path.rename(new_path)
            logging.info(f"[INFO] Fichier déplacé : {archive_path} --> {new_path}")

            # Supprimer l'ancien fichier
            filepath.unlink(missing_ok=True)
            return True

        # Tout est correct
        logging.info(f"[INFO] Catégorie correcte pour {filepath}")
        return True

    except Exception as e:
        logging.error(f"[ERREUR] Échec de la vérification/correction pour {filepath} : {e}")
        return False


def add_archives_to_path(filepath):
    # Créer un objet Path à partir du chemin
    path_obj = Path(filepath)
    
    # Insérer "Archives" entre le dossier parent et le fichier
    archive_path = filepath_obj.parent / "Archives" / filepath_obj.name
    
    return str(archive_path)
