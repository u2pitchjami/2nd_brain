curl -X POST http://192.168.50.12:11434/api/generate \
-H "Content-Type: application/json" \
-d '{
  "model": "llama3:latest",
  "prompt": "Explique le processus de création dune image Docker."
}'


[INFO] Modification significative détectée. Mise à jour des tags et résumé.
[MODIFICATION] /mnt/user/Documents/Obsidian/notes/Clippings
Exception in thread Thread-1:
Traceback (most recent call last):
  File "/usr/lib/python3.12/threading.py", line 1073, in _bootstrap_inner
    self.run()
  File "/home/pipo/bin/.venv/lib/python3.12/site-packages/watchdog/observers/api.py", line 213, in run
    self.dispatch_events(self.event_queue)
  File "/home/pipo/bin/.venv/lib/python3.12/site-packages/watchdog/observers/api.py", line 391, in dispatch_events
    handler.dispatch(event)
  File "/home/pipo/bin/.venv/lib/python3.12/site-packages/watchdog/events.py", line 217, in dispatch
    getattr(self, f"on_{event.event_type}")(event)
  File "/home/pipo/bin/obsidian_scripts/auto_tags.py", line 223, in on_modified
    process_single_note(event.src_path)
  File "/home/pipo/bin/obsidian_scripts/auto_tags.py", line 270, in process_single_note
    with open(filepath, 'r') as file:
         ^^^^^^^^^^^^^^^^^^^
IsADirectoryError: [Errno 21] Is a directory: '/mnt/user/Documents/Obsidian/notes/Clippings'


