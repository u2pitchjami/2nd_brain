from handlers.watcher import start_watcher
import time
import logging


ollama_api_url = "http://192.168.50.12:11434/api/generate"

  # Emplacement du fichier log
logging.basicConfig(filename='/home/pipo/bin/dev/2nd_brain/obsidian_scripts/logs/auto_tags.log', level=logging.DEBUG, format='%(asctime)s - %(message)s')

if __name__ == "__main__":
    start_watcher()