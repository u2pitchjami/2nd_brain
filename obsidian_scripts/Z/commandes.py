import os
import re

notes_folder = "/mnt/user/Documents/Obsidian/notes"
output_file = os.path.join(notes_folder, "Commandes_utiles.md")

def extract_commands_from_notes():
    all_commands = []
    for root, dirs, files in os.walk(notes_folder):
        for file in files:
            if file.endswith(".md"):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    commands = re.findall(r"#command\s+(.+)", content)
                    if commands:
                        all_commands.extend(commands)
    
    # Écrire dans la note récapitulative
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Commandes Utiles\n\n")
        for cmd in all_commands:
            f.write(f"- {cmd}\n")

    print("Commandes utiles extraites avec succès !")

if __name__ == "__main__":
    extract_commands_from_notes()
