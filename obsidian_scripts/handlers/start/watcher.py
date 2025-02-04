from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
from datetime import datetime
from queue import Queue
from handlers.start.process_single_note import process_single_note
from handlers.start.process_note_event import process_note_event
from handlers.start.process_folder_event import process_folder_event  # Nouvelle fonction à créer
import os
import logging
import time

logger = logging.getLogger()

print(f"🔎 {__name__} → Niveau du logger: {logger.level}")
print(f"🔍 Vérif logger {__name__} → Handlers: {logger.handlers}, Level: {logger.level}")

# File d'attente pour les événements
event_queue = Queue()

# Chemin vers le dossier contenant les notes Obsidian
obsidian_notes_folder = os.getenv('BASE_PATH')

# Lancement du watcher pour surveiller les modifications dans le dossier Obsidian
def start_watcher():
    path = obsidian_notes_folder
    observer = PollingObserver()
    observer.schedule(NoteHandler(), path, recursive=True)
    observer.start()
    logging.info(f"[INFO] Démarrage du script, actif sur : {obsidian_notes_folder}")

    try:
        process_queue()  # Lancement de la boucle de traitement de la file d’attente
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

class NoteHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not self.is_hidden(event.src_path):
            event_type = 'directory' if event.is_directory else 'file'
            logging.info(f"[INFO] [CREATION] {event_type.upper()} → {event.src_path}")
            
            # 🎯 Mise à jour immédiate de note_paths.json
            if event_type == 'file' and event.src_path.endswith('.md'):
                logging.info(f"[DEBUG] Traitement de l'événement : {event_type}")
                process_note_event({'path': event.src_path, 'action': 'created'})
            elif event_type == 'directory':
                process_folder_event({'path': event.src_path, 'action': 'created'})
            
            # 🌀 Envoi dans la file pour traitement asynchrone (ex : import)
            if event_type == 'file' and event.src_path.endswith('.md'):
                event_queue.put({'type': 'file', 'action': 'created', 'path': event.src_path})

    def on_deleted(self, event):
        if not self.is_hidden(event.src_path):
            event_type = 'directory' if event.is_directory else 'file'
            logging.info(f"[INFO] [SUPPRESSION] {event_type.upper()} → {event.src_path}")
            
            # 🎯 Mise à jour immédiate de note_paths.json
            if event_type == 'file' and event.src_path.endswith('.md'):
                process_note_event({'path': event.src_path, 'action': 'deleted'})
            elif event_type == 'directory':
                process_folder_event({'path': event.src_path, 'action': 'deleted'})
            
            # Pas forcément besoin d’envoyer en file d'attente sauf pour traitements spéciaux

    def on_modified(self, event):
        if not event.is_directory and not self.is_hidden(event.src_path):
            logging.info(f"[INFO] [MODIFICATION] FILE → {event.src_path}")
            
            # 🎯 Mise à jour immédiate de note_paths.json
            process_note_event({'path': event.src_path, 'action': 'modified'})
            
            # 🌀 Envoi en file d'attente pour traitement lourd si nécessaire
            event_queue.put({'type': 'file', 'action': 'modified', 'path': event.src_path})

    def on_moved(self, event):
        if not self.is_hidden(event.src_path) and not self.is_hidden(event.dest_path):
            event_type = 'directory' if event.is_directory else 'file'
            logging.info(f"[INFO] [DÉPLACEMENT] {event_type.upper()} → {event.src_path} -> {event.dest_path}")
            
            # 🎯 Mise à jour immédiate de note_paths.json pour le déplacement
            if event_type == 'file' and event.src_path.endswith('.md'):
                process_note_event({'path': event.src_path, 'action': 'deleted'})  # Supprimer l'ancien
                process_note_event({'path': event.dest_path, 'action': 'created'})  # Ajouter le nouveau
            elif event_type == 'directory':
                process_folder_event({'path': event.src_path, 'action': 'deleted'})
                process_folder_event({'path': event.dest_path, 'action': 'created'})
            
            # 🌀 Envoi en file d'attente si des traitements doivent être faits après le déplacement
            event_queue.put({
                'type': event_type,
                'action': 'moved',
                'src_path': event.src_path,
                'dest_path': event.dest_path
            })

    @staticmethod
    def is_hidden(path):
        return any(part.startswith('.') for part in path.split(os.sep))


def process_queue():
    while True:
        try:
            event = event_queue.get()  # Timeout pour éviter un blocage
            logging.debug(f"[DEBUG] Event récupéré depuis la file : {event}")

            if event['type'] == 'file':
                if event['action'] == 'moved':
                    process_single_note(event['src_path'], event['dest_path'])
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

            log_event_queue(event_queue)
            event_queue.task_done()
        except Exception as e:
            logging.error(f"[ERREUR] Erreur dans le traitement de la file d'attente : {e}")
            time.sleep(1)  # Attendre avant de vérifier à nouveau pour éviter une boucle infinie en cas d'erreur

def log_event_queue(queue):
    logging.info(f"[DEBUG] Contenu de la file d'attente : {list(queue.queue)}")
