import os
from dotenv import load_dotenv
import anthropic

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Récupérer la clé API depuis les variables d'environnement
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

# Vérifier si la clé API est présente
if not anthropic_api_key:
    raise ValueError("La clé API Anthropic n'a pas été trouvée dans le fichier .env")

# Initialiser le client Anthropic
client = anthropic.Anthropic(api_key=anthropic_api_key)

# Fonction pour dialoguer avec Claude
def chat_with_claude(prompt):
    message = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        temperature=0,
        system="Vous êtes un assistant IA utile et concis.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return message.content

# Exemple d'utilisation
prompt = "Dis-moi bonjour en français."
response = chat_with_claude(prompt)
print("Claude dit:", response)
