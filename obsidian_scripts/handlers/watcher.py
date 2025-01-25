from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
from datetime import datetime
from handlers.process_single_note import process_single_note
import os
import logging
import time

logger = logging.getLogger(__name__)



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
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    
class NoteHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not self.is_hidden(event.src_path):
            logging.info(f"[INFO] [MODIFICATION] {event.src_path}")
            process_single_note(event.src_path)
    
    def on_created(self, event):
        if not self.is_hidden(event.src_path):
            logging.info(f"[INFO] [CREATION] {event.src_path}")
            process_single_note(event.src_path)
    
    def on_deleted(self, event):
        if not self.is_hidden(event.src_path):
            logging.info(f"[INFO] [SUPPRESSION] {event.src_path}")
            process_single_note(event.src_path)
    
    def on_moved(self, event):
        if not self.is_hidden(event.src_path) and not self.is_hidden(event.dest_path):
            logging.info(f"[INFO] [DEPLACEMENT] {event.src_path} -> {event.dest_path}")
            process_single_note(event.dest_path)
    @staticmethod
    def is_hidden(path):
        # Vérifie si le dossier ou fichier est caché (commence par un .)
        return any(part.startswith('.') for part in path.split(os.sep))