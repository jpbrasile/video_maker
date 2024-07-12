import os
from dotenv import load_dotenv

# Charger le fichier .env
load_dotenv()

# Récupérer la clé API
api_key = os.getenv('ANTHROPIC_API_KEY')

# Vérifier si la clé API est chargée
if not api_key:
    raise ValueError("La clé API n'est pas définie dans le fichier .env")

# Exporter la clé API en tant que variable d'environnement
os.environ['ANTHROPIC_API_KEY'] = api_key

# Exécuter la commande pour lancer aider
os.system('aider')
