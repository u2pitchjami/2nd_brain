import os
from datetime import datetime
from handlers.ollama import get_summary_from_ollama
from handlers.ollama import get_tags_from_ollama
from handlers.divers import count_words
import logging

# Fonction pour ajouter ou mettre à jour les tags, résumés et commandes dans le front matter YAML
def add_metadata_to_yaml(filepath, tags, summary):
    try:    
        logging.debug(f"[DEBUG] add_yaml : démarrage fonction : {filepath}")
        with open(filepath, "r", encoding="utf-8") as file:
            lines = file.readlines()
            logging.debug(f"[DEBUG] add_yaml : lines : {lines}")
                
        nombre_mots = count_words("".join(lines))
        logging.debug(f"[DEBUG] add_yaml : nb de mots {nombre_mots} : {filepath}")
        date_actuelle = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.debug(f"[DEBUG] add_yaml : date {date_actuelle} : {filepath}")
        # Récupération de la date de création existante ou initialisation
        date_creation = date_actuelle
        yaml_start, yaml_end = -1, -1
        logging.debug(f"[DEBUG] add_yaml : recherche de l'entête : {filepath}")
        if lines[0].strip() == "---":
            yaml_start = 0
            # Recherche la fin de l'entête YAML
            yaml_end = next((i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---"), -1)
        else:
            yaml_start = -1
            yaml_end = -1
        for i, line in enumerate(lines):
            #logging.debug(f"[DEBUG] add_yaml i : {i} : {line}")
        #    if line.strip() == "---":
        #        logging.debug(f"[DEBUG] add_yaml i : {i} :yaml_start {yaml_start} : {line}")
        #       if yaml_start == -1:
        #            yaml_start = i
        #            logging.debug(f"[DEBUG] add_yaml i : {i} :yaml_start {yaml_start} : {filepath}")
        #        else:
        #            yaml_end = i
        #            logging.debug(f"[DEBUG] add_yaml i : {i} :yaml_end {yaml_end} : {line}")
        #            break
            if line.startswith("created:"):
                logging.debug(f"[DEBUG] add_yaml i : {i} : ligne created")
                date_creation = line.split(":")[1].strip()
            #if line.startswith("source:"):
            #    logging.debug(f"[DEBUG] add_yaml i : {i} : ligne source")
            #    source_yaml = line.split(":")[1].strip()
        logging.debug(f"[DEBUG] add_yaml : Y a t-il une entête ?")
        logging.debug(f"[DEBUG] add_yaml : yaml start : {yaml_start} , yaml end : {yaml_end}")
        # Si aucune entête YAML n'existe, la créer
        if yaml_start == -1 or yaml_end == -1:
            logging.debug(f"[DEBUG] add_yaml : Création de l'entête")
            missing_summary = not any("summary:" in line for line in lines[yaml_start:yaml_end])
            missing_tags = not any("tags:" in line for line in lines[yaml_start:yaml_end])

            if missing_tags:
                #logging.debug(f"[DEBUG] add_yaml : Création des tags pour l'entête")
                lines.insert(yaml_end, f"tags: [{', '.join(tags)}]\n")
                logging.info(f"Ajout des tags manquants pour {filepath}")

            if missing_summary:
                #logging.debug(f"[DEBUG] add_yaml : Création du résumé pour l'entête")
                lines.insert(yaml_end, f"summary: |\n  {summary.replace('\n', '\n  ')}\n")
                logging.info(f"Ajout du résumé manquant pour {filepath}")
                
            yaml_block = [
                "---\n",
                f"tags: [{', '.join(tags)}]\n",
                f"summary: |\n  {summary.replace('\n', '\n  ')}\n",
                f"word_count: {nombre_mots}\n",
                f"created: {date_creation}\n",
                f"last_modified: {date_actuelle}\n",
                #f"source: {source_yaml}\n",
                "author: \n",
                "status: \n",
                "---\n\n"
            ]
            lines = yaml_block + lines
            logging.info(f"Création d'une entête YAML complète pour {filepath} :\n{''.join(yaml_block)}")
            #logging.debug(f"[DEBUG] add_yaml : Création d'une entête YAML complète pour {filepath} :\n{''.join(yaml_block)}")
        
        else:
            # Mise à jour des métadonnées existantes
            logging.debug(f"[DEBUG] add_yaml : Il y a déjà une entête")
            inside_yaml = False
            inside_summary = False
            inside_tags = False
            logging.debug(f"[DEBUG] add_yaml : recherche des lignes à traiter")
            for i in range(yaml_start, yaml_end):
                line = lines[i].strip()

                # Détecte les lignes à traiter
                if line == "---":
                    logging.debug(f"[DEBUG] add_yaml ligne {i} : {line}")
                    inside_yaml = not inside_yaml

                if inside_yaml:
                    if line.startswith("tags:"):
                        logging.debug(f"[DEBUG] add_yaml ligne tags {i} : {line}")
                        inside_tags = True
                        logging.debug(f"[DEBUG] add_yaml : la ligne tags existe")
                        lines[i] = f"tags: [{', '.join(tags)}]\n"
                        logging.debug(f"[DEBUG] add_yaml : nouvelle valeur de tags: [{', '.join(tags)}]\n")
                    elif inside_tags and line.startswith("  - "):
                        lines[i] = ""  # Efface les anciennes lignes de tags
                    else:
                        inside_tags = False

                    if line.startswith("summary:"):
                        inside_summary = True
                        logging.debug(f"[DEBUG] add_yaml : la ligne résumé existe")
                        lines[i] = f"summary: |\n  {summary.replace('\n', '\n  ')}\n"
                        logging.debug(f"[DEBUG] add_yaml : nouvelle valeur de résumé {summary.replace('\n', '\n  ')}")
                    elif inside_summary and line.startswith("  "):
                        lines[i] = ""  # Efface les anciennes lignes du résumé
                    else:
                        inside_summary = False

                    if line.startswith("word_count:"):
                        logging.debug(f"[DEBUG] add_yaml : la ligne word_count existe")
                        lines[i] = f"word_count: {nombre_mots}\n"
                        logging.debug(f"[DEBUG] add_yaml : nouvelle valeur de nb mots {nombre_mots}")

                    if line.startswith("last_modified:"):
                        logging.debug(f"[DEBUG] add_yaml : la ligne last_modified existe")
                        lines[i] = f"last_modified: {date_actuelle}\n"
                        logging.debug(f"[DEBUG] add_yaml : nouvelle valeur de last_modified: {date_actuelle}")

                       
                        
            # Loguer l'entête après modification
            yaml_block = lines[yaml_start:yaml_end + 1]
            logging.info(f"[YAML MODIFIÉ] pour {filepath} :\n{''.join(yaml_block)}")
            
            missing_summary = not any("summary:" in line for line in lines[yaml_start:yaml_end])
            missing_tags = not any("tags:" in line for line in lines[yaml_start:yaml_end])

            if missing_tags:
                lines.insert(yaml_end, f"tags: [{', '.join(tags)}]\n")
                logging.debug(f"[DEBUG] add_yaml : la ligne tags manquante, ajout de tags: [{', '.join(tags)}] ")
            if missing_summary:
                lines.insert(yaml_end, f"summary: |\n  {summary.replace('\n', '\n  ')}\n")
                logging.debug(f"[DEBUG] add_yaml : la ligne résumé manquante, ajout de {summary.replace('\n', '\n  ')} ")

                
        # Écriture des modifications dans le fichier
        with open(filepath, "w", encoding="utf-8") as file:
            file.writelines(lines)
            logging.info(f"Fichier {filepath} mis à jour avec succès.")
            logging.debug(f"[DEBUG] add_yaml : fichier mis à jour {filepath}")
    
    except Exception as e:
        logging.error(f"Erreur lors de la mise à jour de {filepath} : {e}")
        raise
   
def make_properties(content, filepath):
    """
    génère les entêtes.
    """
    logging.debug(f"[DEBUG] make_pro : Entrée de la fonction de {filepath}")
    #print ("make",filepath)
    logging.debug(f"[DEBUG] make_pro : Récupération des tags pour {filepath}")
    tags = get_tags_from_ollama(content)
    logging.debug(f"[DEBUG] make_pro : Récupération du résumé pour {filepath}")
    summary = get_summary_from_ollama(content)
    logging.debug(f"[DEBUG] make_pro : Yaml pour {filepath}")
    add_metadata_to_yaml(filepath, tags, summary)
    

    # Relecture et comptage après mise à jour complète
    with open(filepath, 'r', encoding='utf-8') as file:
        updated_content = file.read()
        logging.debug(f"[DEBUG] make_pro : relecture du fichier : {filepath}")
    nombre_mots_actuels = count_words(updated_content)
    logging.debug(f"[DEBUG] make_pro : recomptage du nb de mots pour : {filepath} ")

    # Mise à jour du word_count immédiatement
    with open(filepath, "r", encoding="utf-8") as file:
        lines = file.readlines()

    with open(filepath, "w", encoding="utf-8") as file:
        word_count_updated = False
        for i, line in enumerate(lines):
            if line.startswith("word_count:"):
                logging.debug(f"[DEBUG] make_pro : mise à jour du nb de mots : {filepath}")
                lines[i] = f"word_count: {nombre_mots_actuels}\n"
                word_count_updated = True
                break
        else:
            # Ajoute word_count s'il n'existe pas
            logging.debug(f"[DEBUG] make_pro : ajout du nb de mots (car inexistant) : {filepath}")
            lines.insert(3, f"word_count: {nombre_mots_actuels}\n")

        file.writelines(lines)

    logging.info(f"Nombre de mots mis à jour pour {filepath}")
    logging.debug(f"[DEBUG] make_pro : fin du process de mise à jour du nb de mots : {filepath}")
    return