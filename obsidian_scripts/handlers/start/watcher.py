from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
from datetime import datetime
from queue import Queue
from handlers.start.process_single_note import process_single_note
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
    logging.info(f"[INFO] démarrage du script, \n active sur : {obsidian_notes_folder} ")

    try:
        # Lancement de la boucle de traitement de la file d’attente
        process_queue()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
     
class NoteHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory and not self.is_hidden(event.src_path):
            logging.info(f"[INFO] [MODIFICATION] {event.src_path}")
            event_queue.put(event.src_path)  # Ajout dans la file d'attente

    def on_created(self, event):
        if not event.is_directory and not self.is_hidden(event.src_path):
            logging.info(f"[INFO] [CREATION] {event.src_path}")
            event_queue.put(event.src_path)  # Ajout dans la file d'attente

    def on_deleted(self, event):
        if not event.is_directory and not self.is_hidden(event.src_path):
            logging.info(f"[INFO] [SUPPRESSION] {event.src_path}")
            event_queue.put(event.src_path)  # Ajout dans la file d'attente

    def on_moved(self, event):
        if not event.is_directory and not self.is_hidden(event.src_path) and not self.is_hidden(event.dest_path):
            logging.info(f"[INFO] [DEPLACEMENT] {event.src_path} -> {event.dest_path}")
            event_queue.put((event.src_path, event.dest_path))  # Envoi des deux chemins

    @staticmethod
    def is_hidden(path):
        # Vérifie si le dossier ou fichier est caché (commence par un .)
        return any(part.startswith('.') for part in path.split(os.sep))
    
def process_queue():
    while True:
        try:
            #event = event_queue.get()
            filepath = event_queue.get()  # Timeout pour éviter un blocage
            logging.debug(f"[DEBUG] Event récupéré depuis la file : {filepath}")
            logging.debug(f"[DEBUG] Event récupéré depuis la file : {type(filepath)}")
            if isinstance(filepath, tuple):  # Vérifie si c'est un déplacement (src, dest)
                src_path, dest_path = filepath
                process_single_note(src_path, dest_path)
            else:  # Sinon, traite comme un chemin simple (par exemple, pour on_created)
                process_single_note(filepath)

            log_event_queue(event_queue)
            event_queue.task_done()
        except Exception as e:
            logging.error(f"[ERREUR] Erreur dans le traitement de la file d'attente : {e}")
            logging.debug("[DEBUG] Aucune tâche en attente dans la file.")
        
    #    try:
            # Récupère un fichier de la file d’attente
    #        filepath = event_queue.get(timeout=5)  # Timeout pour éviter un blocage
    #        logging.info(f"[INFO] Traitement du fichier : {filepath}")
    #        process_single_note(filepath)  # Appelle ta fonction principale pour le traitement
    #        event_queue.task_done()  # Signale que le traitement est terminé
    #    except Exception as e:
    #        logging.debug("[DEBUG] Aucune tâche en attente dans la file.")
    #        time.sleep(1)  # Attend avant de vérifier à nouveau
    
def log_event_queue(queue):
    """ Affiche le contenu de la queue """
    logging.info(f"[DEBUG] Contenu de la file d'attente : {list(queue.queue)}")