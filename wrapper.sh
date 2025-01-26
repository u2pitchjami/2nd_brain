#!/bin/bash

# === CONFIGURATION ===
ENV_PATH="/home/pipo/bin/.venv"  # Chemin de l'environnement virtuel
SCRIPT_PATH="/home/pipo/bin/2nd_brain/obsidian_scripts/check.py"  # Chemin absolu du script Python

# Activer l'environnement virtuel
if [ -d "$ENV_PATH" ]; then
    source "$ENV_PATH/bin/activate"
else
    echo "[$(date)] ERREUR : Environnement virtuel introuvable : $ENV_PATH"
    exit 1
fi

# Exécuter le script Python
if [ -f "$SCRIPT_PATH" ]; then
    python "$SCRIPT_PATH"
else
    echo "[$(date)] ERREUR : Script introuvable : $SCRIPT_PATH"
    deactivate
    exit 1
fi

# Désactiver l'environnement virtuel
deactivate
