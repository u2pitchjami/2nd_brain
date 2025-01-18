from pathlib import Path

DIRS = {
    "technical": Path("/mnt/user/Documents/Obsidian/notes/Technique"),
    "imports": Path("/mnt/user/Documents/Obsidian/notes/imports"),
    "tutorial": Path("/mnt/user/Documents/Obsidian/notes/Tutorial"),
    "idea": Path("/mnt/user/Documents/Obsidian/notes/Idées"),
    "news": Path("/mnt/user/Documents/Obsidian/notes/News"),
    "todo": Path("/mnt/user/Documents/Obsidian/notes/Todo"),
    "unknown": Path("/mnt/user/Documents/Obsidian/notes/unknown"),
    "synthèses_import": Path("/mnt/user/Documents/Obsidian/notes/synthèses_import"),
    "synthèses_processed": Path("/mnt/user/Documents/Obsidian/notes/synthèses_processed")
}
NOTE_PATHS = {
    "notes/Technique": {"category": "technical", "subcategory": "article"},
    "notes/News": {"category": "news", "subcategory": "article"},
    "notes/Idées": {"category": "idea", "subcategory": "thought"},
    "notes/Todo": {"category": "todo", "subcategory": "task"},
    "notes/Tutorial": {"category": "tutorial", "subcategory": "guide"}
}

