import os
from handlers.import_gpt import process_import_gpt
from handlers.import_normal import import_normal
import logging

def process_single_note(filepath):
    logging.debug(f"[DEBUG] démarrage du process_single_note pour : {filepath}")
    
    if not os.path.exists(filepath):
        logging.warning(f"[WARNING] Le fichier n'existe pas ou plus : {filepath}")
        return
    
    if not filepath.endswith(".md"):
        return
    
    # Obtenir le dossier contenant le fichier
    base_folder = os.path.dirname(filepath)

    # Vérifie si le fichier vient de 'gpt_import'
    if "gpt_import" in base_folder:
        print(f"Le fichier {filepath} vient de gpt_import.")
        # Appeler la fonction spécifique
        process_import_gpt(filepath)
    elif "synthèses_import" in base_folder:
        print(f"Le fichier {filepath} vient de 'synthèses_import'.")
        # Appeler une autre fonction
        process_import_syntheses(filepath)
        return
    elif "processed" in base_folder:
        print(f"Le fichier {filepath} vient de 'processed'.")
        # Appeler une autre fonction
        return
    else:
        print(f"Le fichier {filepath} vient d'ailleurs : traitement normal")
        # Appeler une autre fonction
        import_normal(filepath) 
    