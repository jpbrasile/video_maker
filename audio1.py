import os
from dotenv import load_dotenv
from openai import OpenAI

# Charger les variables d'environnement
load_dotenv()

# Récupérer la clé API OpenAI
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialiser le client OpenAI
client = OpenAI(api_key=openai_api_key)

def text_to_speech(text, output_path):
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )

        # Écrire directement le contenu de la réponse dans un fichier
        with open(output_path, 'wb') as file:
            file.write(response.content)
        
        print(f"Fichier audio créé avec succès : {output_path}")
    except Exception as e:
        print(f"Erreur lors de la création du fichier audio : {str(e)}")

def main():
    # Définir les chemins des fichiers
    input_file = "output/voice_over_1.txt"
    output_file = "output/audio_1.mp3"

    # Lire le contenu du fichier texte
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            voice_over_text = file.read().strip()
    except FileNotFoundError:
        print(f"Le fichier {input_file} n'a pas été trouvé.")
        return
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier : {str(e)}")
        return

    # Créer le fichier audio
    text_to_speech(voice_over_text, output_file)

if __name__ == "__main__":
    main()