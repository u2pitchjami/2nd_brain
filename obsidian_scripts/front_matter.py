def add_tags_to_yaml(filepath, tags):
    with open(filepath, 'r') as file:
        lines = file.readlines()
    
    # Vérifier si le fichier a déjà un front matter
    if lines[0].strip() != "---":
        lines.insert(0, "---\n")
        lines.insert(1, f"tags: [{', '.join(tags)}]\n")
        lines.insert(2, "---\n\n")
    else:
        # Ajouter ou mettre à jour les tags dans le front matter existant
        for i, line in enumerate(lines):
            if line.strip().startswith("tags:"):
                lines[i] = f"tags: [{', '.join(tags)}]\n"
                break
        else:
            for i, line in enumerate(lines):
                if line.strip() == "---":
                    lines.insert(i, f"tags: [{', '.join(tags)}]\n")
                    break
    
    with open(filepath, 'w') as file:
        file.writelines(lines)
        
        
        
        
        
        
        
        keywords_to_tags = {
    "Docker": "#docker",
    "Python": "#python",
    "Automatisation": "#automation",
}

def simple_tagging(content):
    tags = [tag for keyword, tag in keywords_to_tags.items() if keyword in content]
    return tags