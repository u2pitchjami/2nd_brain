import os
import json
import subprocess
import requests
from datetime import datetime, UTC, timedelta

UNRAID_SERVER = "http://192.168.50.12:5050/receive"
TRACKING_FILE = "/home/pipo/bin/2nd_brain/activity/process_tracking.json"

IGNORED_PROCESSES = ["kworker", "rcu_preempt", "migration", "watchdog", "idle"]

def get_recent_commands():
    """Récupère les 10 dernières commandes avec leur horodatage"""
    history_file = os.path.expanduser("~/.bash_history")  
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            commands = f.readlines()

        last_command_time = datetime.now(UTC)
        if commands:
            last_command_time = datetime.fromtimestamp(os.path.getmtime(history_file), UTC)

        idle_time = (datetime.now(UTC) - last_command_time).total_seconds() / 60  # Minutes
        return {
            "last_command": commands[-1].strip() if commands else "None",
            "last_command_time": last_command_time.isoformat(),
            "idle_time_minutes": round(idle_time, 2)
        }
    
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de l'historique : {e}")
        return {}


def get_active_processes():
    """Liste uniquement les applications ouvertes par l'utilisateur courant"""
    command = "ps -u $(whoami) -o comm --sort=-%cpu | tail -n +2"
    output = subprocess.run(command, shell=True, capture_output=True, text=True)
    processes = output.stdout.strip().split("\n")

    return [
        {"timestamp": datetime.now(UTC).isoformat(), "process": p.strip()}
        for p in processes if p.strip() and not any(ignore in p for ignore in IGNORED_PROCESSES)
    ][:10]

def track_persistent_processes(process_list):
    """Compare avec les anciens processus pour détecter ceux qui restent ouverts longtemps"""
    if os.path.exists(TRACKING_FILE):
        with open(TRACKING_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
    else:
        history = {}

    now = datetime.now(UTC)
    updated_history = {}

    # Vérifier la durée des processus
    for proc in process_list:
        name = proc["process"]
        if name in history:
            start_time = datetime.fromisoformat(history[name])
            duration = (now - start_time).total_seconds() / 60  # Minutes
            if duration > 15:  # Seuil de 15 minutes
                updated_history[name] = history[name]  # Garde le process s'il est toujours actif
        else:
            updated_history[name] = now.isoformat()  # Nouveau process

    # Sauvegarde la nouvelle liste des processus suivis
    with open(TRACKING_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_history, f, indent=4)

    # Retourne uniquement les process détectés comme "persistants"
    return [{"process": p, "start_time": updated_history[p]} for p in updated_history]

# Capture des processus actifs
active_processes = get_active_processes()
persistent_processes = track_persistent_processes(active_processes)

# Création du contexte à envoyer
context = {
    "hostname": os.uname().nodename,
    "timestamp": datetime.now(UTC).isoformat(),
    "persistent_apps": persistent_processes
}

# Envoi des données à Unraid
try:
    response = requests.post(UNRAID_SERVER, json=context)
    print(f"✅ Données envoyées à Unraid : {response.status_code} - {response.json()}")
except Exception as e:
    print(f"❌ Erreur lors de l'envoi des données : {e}")
