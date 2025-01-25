from pathlib import Path

NOTE_PATHS = {
    "notes/Informatique/Python": {
        "category": "informatique", 
        "subcategory": "python",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Informatique/Python"),
        "prompt_name": "article",
        "explanation": "note about python programming language"
        },
    "notes/Informatique/Bash": {
        "category": "informatique", 
        "subcategory": "bash",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Informatique/Bash"),
        "prompt_name": "article",
        "explanation": "note about bash or sh programming language"
        },
    "notes/Informatique/AI": {
        "category": "informatique", 
        "subcategory": "ai",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Informatique/AI"),
        "prompt_name": "article",
        "explanation": "theoretical or practical note about artificial intelligence (software, prompt, evolution, perspective) but not ai or bot conversation"
        },
    "notes/Informatique/Docker": {
        "category": "informatique", 
        "subcategory": "docker",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Informatique/Docker"),
        "prompt_name": "article",
        "explanation": "note about docker"
        },
    "notes/Informatique/Linux": {
        "category": "informatique", 
        "subcategory": "linux",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Informatique/Linux"),
        "prompt_name": "article",
        "explanation": "note about linux systems (debian, red hat, raspberry, mint, etc...)"
        },
    "notes/Informatique/Windows": {
        "category": "informatique", 
        "subcategory": "windows",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Informatique/Windows"),
        "prompt_name": "article",
        "explanation": "note about windows systems"
        },
    "notes/Informatique/Unraid": {
        "category": "informatique", 
        "subcategory": "unraid",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Informatique/Unraid"),
        "prompt_name": "article",
        "explanation": "note about Unraid OS"
        },
    "notes/Informatique/Divers": {
        "category": "informatique", 
        "subcategory": "divers",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Informatique/Divers"),
        "prompt_name": "divers",
        "explanation": "Notes related to generaly or informational articles about IT, hardware, software"
        },
    "notes/Cinéma/Divers": {
        "category": "cinema", 
        "subcategory": "divers",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Cinéma/divers"),
        "prompt_name": "divers",
        "explanation": "Notes related to movie reviews or critique"
        },
    "notes/Cinéma/Reviews": {
        "category": "cinema", 
        "subcategory": "reviews",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Cinéma/Reviews"),
        "prompt_name": "divers",
        "explanation": "General notes about cinema"
        },
    "notes/Cinéma/Watchlist": {
        "category": "cinema", 
        "subcategory": "watchlist",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Cinéma/Watchlist"),
        "prompt_name": "watchlist",
        "explanation": "Notes related to lists of movies to watch or watched and recommandations"
        },
    "notes/Gaming/Reviews": {
        "category": "gaming", 
        "subcategory": "reviews",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Gaming/Reviews"),
        "prompt_name": "divers",
        "explanation": "Notes related to Reviews or critiques of video games"
        },
    "notes/Gaming/Divers": {
        "category": "gaming", 
        "subcategory": "divers",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Gaming/Divers"),
        "prompt_name": "divers",
        "explanation": "Notes related to"
        },
    "notes/Gaming/Guide": {
        "category": "gaming", 
        "subcategory": "guide",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Gaming/Guide"),
        "prompt_name": "divers",
        "explanation": "Notes related to Guides or tips for specific games"
        },
    "notes/Gaming/Playlist": {
        "category": "gaming", 
        "subcategory": "playlist",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Gaming/Playlist"),
        "prompt_name": "watchlist",
        "explanation": "Notes related to Lists of games to play or played or recommandations"
        },
    "notes/Musique/Ableton": {
        "category": "music", 
        "subcategory": "ableton",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Musique/Ableton"),
        "prompt_name": "divers",
        "explanation": "Notes related to Ableton software for music production"
        },
    "notes/Musique/Divers": {
        "category": "music", 
        "subcategory": "divers",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Musique/Divers"),
        "prompt_name": "divers",
        "explanation": "General notes about music"
        },
    "notes/Musique/Artistes": {
        "category": "music", 
        "subcategory": "artist",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Musique/Artistes"),
        "prompt_name": "divers",
        "explanation": "Notes related to about musical artists"
        },
    "notes/Musique/Playlist": {
        "category": "music", 
        "subcategory": "playlist",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Musique/Playlist"),
        "prompt_name": "watchlist",
        "explanation": "Notes related to Music playlists or played or recommendations"
        },
    "notes/Lifestyle/Bricolage": {
        "category": "lifestyle", 
        "subcategory": "diy",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Lifestyle/Bricolage"),
        "prompt_name": "divers",
        "explanation": "Notes related to DIY projects or bricolage"
        },
    "notes/Lifestyle/Divers": {
        "category": "lifestyle", 
        "subcategory": "divers",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Lifestyle/Divers"),
        "prompt_name": "divers",
        "explanation": "General notes about lifestyle"
        },
    "notes/Lifestyle/Chats": {
        "category": "lifestyle", 
        "subcategory": "pets",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Lifestyle/Chats"),
        "prompt_name": "divers",
        "explanation": "Notes related to pets, like cats or dogs"
        },
    "notes/Lifestyle/Recettes": {
        "category": "lifestyle", 
        "subcategory": "cooking",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Lifestyle/Recettes"),
        "prompt_name": "divers",
        "explanation": "Notes related to Recipes or cooking tips"
        },
    "notes/Agora/Divers": {
        "category": "agora", 
        "subcategory": "divers",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Agora/Divers"),
        "prompt_name": "divers",
        "explanation": "General notes about society"
        },
    "notes/Agora/Géopolitique": {
        "category": "agora", 
        "subcategory": "geopolitics",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Agora/Géopolitique"),
        "prompt_name": "geopolitical",
        "explanation": "Notes related to geopolitics and international relations"
        },
    "notes/Agora/Politique": {
        "category": "agora", 
        "subcategory": "politics",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Agora/Politique"),
        "prompt_name": "political",
        "explanation": "Notes related to politics or political analysis"
        },
    "notes/Agora/Sociologie": {
        "category": "agora", 
        "subcategory": "sociology",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Agora/Sociologie"),
        "prompt_name": "sociology",
        "explanation": "Notes related to sociology or social theories"
        },
    "notes/Sports/Divers": {
        "category": "sports", 
        "subcategory": "divers",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Sports/Divers"),
        "prompt_name": "divers",
        "explanation": "General sports-related notes exept cyclism or football"
        },
    "notes/Sports/Cyclisme": {
        "category": "sports", 
        "subcategory": "cyclism",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Sports/Cyclisme"),
        "prompt_name": "divers",
        "explanation": "Notes related to cycling or related activities (road, track, cyclocross)"
        },
    "notes/Sports/Foot": {
        "category": "sports", 
        "subcategory": "football",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Sports/Foot"),
        "prompt_name": "divers",
        "explanation": "Notes related to football or soccer"
        },
    "notes/Todo": {
        "category": "todo",
        "subcategory": "todo",
        "path": Path("/mnt/user/Documents/Obsidian/notes/Todo"),
        "prompt_name": "todo",
        "explanation": "todo list"
        },
    "notes/unknown": {
        "category": "unknown",
        "subcategory": "unknown",
        "path": Path("/mnt/user/Documents/Obsidian/notes/unknown")
        },
    "notes/gpt_import": {
        "category": "conversation_GPT",
        "subcategory": "conversation_GPT",
        "path": Path("/mnt/user/Documents/Obsidian/notes/gpt_import"),
        "prompt_name": "divers",
        "explanation": "Notes related to a bot or gpt conversation"
        }
    
}