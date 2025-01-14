import os
import shutil
from datetime import datetime
import logging

def copy_file_with_date(filepath, destination_folder):
    """
    Copie un fichier en ajoutant la date au nom.
    """
    try:
        # Obtenir le nom de base du fichier
        filename = os.path.basename(filepath)
        
        # Extraire le nom et l'extension du fichier
        name, ext = os.path.splitext(filename)
        
        # Obtenir la date actuelle au format souhaité
        date_str = datetime.now().strftime("%y%m%d")  # Exemple : '250112'
        
        # Construire le nouveau nom avec la date
        new_filename = f"{date_str}_{name}{ext}"
        
        # Construire le chemin complet de destination
        destination_path = os.path.join(destination_folder, new_filename)
        
        # Déplacer le fichier
        shutil.copy(filepath, destination_path)
        
        print(f"Fichier copié avec succès : {destination_path}")
    except Exception as e:
        print(f"Erreur lors de la copie du fichier : {e}")
        
def move_file_with_date(filepath, destination_folder):
    """
    déplace un fichier en ajoutant la date au nom.
    """
    try:
        # Obtenir le nom de base du fichier
        filename = os.path.basename(filepath)
        
        # Extraire le nom et l'extension du fichier
        name, ext = os.path.splitext(filename)
        
        # Obtenir la date actuelle au format souhaité
        date_str = datetime.now().strftime("%y%m%d")  # Exemple : '250112'
        
        # Construire le nouveau nom avec la date
        new_filename = f"{date_str}_{name}{ext}"
        
        # Construire le chemin complet de destination
        destination_path = os.path.join(destination_folder, new_filename)
        
        # Déplacer le fichier
        shutil.move(filepath, destination_path)
        
        print(f"Fichier déplacé avec succès : {destination_path}")
    except Exception as e:
        print(f"Erreur lors du déplacement du fichier : {e}")