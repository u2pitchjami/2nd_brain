from handlers.utils.note_index import update_note_index, remove_note_from_index
from handlers.start.process_folder_event import process_folder_event 
from queue import Queue
import logging
import os

# Création de la file d'attente unique
event_queue = Queue()

def process_queue():
    from handlers.start.process_single_note import process_single_note
    while True:
        try:
            event = event_queue.get()
            logging.debug(f"[DEBUG] Event récupéré depuis la file : {event}")

            if event['type'] == 'file':
                if event['action'] == 'moved':
                    logging.debug(f"[DEBUG] Queue test moved : {event['dest_path']}")
                    if not os.path.exists(event['dest_path']):
                        logging.warning(f"[WARNING] Le fichier n'existe pas ou plus : {event['dest_path']}")
                        continue
                    else:
                        process_single_note(event['src_path'], event['dest_path'])
                else:
                    logging.debug(f"[DEBUG] Queue test not moved : {event['path']}")
                    if not os.path.exists(event['path']):
                        logging.warning(f"[WARNING] Le fichier n'existe pas ou plus : {event['path']}")
                        continue
                    else:
                        process_single_note(event['path'])
            elif event['type'] == 'directory':
                if event['action'] == 'moved':
                    # Traiter le déplacement d'un dossier comme une création pour le nouveau nom
                    process_folder_event({'action': 'created', 'path': event['dest_path']})
                    # Optionnel : Supprimer l'ancienne entrée si elle existait
                    process_folder_event({'action': 'deleted', 'path': event['src_path']})
                else:
                    process_folder_event(event)

            if event:  # Vérifier si l'event est bien formé
                logging.debug("[DEBUG] L'événement est bien détecté, traitement en cours...")
            else:
                logging.error("[ERREUR] Event vide récupéré, suppression forcée.")
            
            log_event_queue()
            event_queue.task_done()
        except Exception as e:
            logging.error(f"[ERREUR] Erreur dans le traitement de la file d'attente : {e}")
            time.sleep(1)  # Attendre avant de vérifier à nouveau pour éviter une boucle infinie en cas d'erreur


def log_event_queue():
    """Affiche le contenu de la file d'attente"""
    logging.info(f"[DEBUG] Contenu de la file d'attente : {list(event_queue.queue)}")
