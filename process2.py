import os
import requests
from dotenv import load_dotenv
from openai import OpenAI

# Charger les variables d'environnement
load_dotenv()

# Récupérer la clé API OpenAI depuis les variables d'environnement
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialiser le client OpenAI
client = OpenAI(api_key=openai_api_key)

def generate_image(prompt):
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        # L'URL de l'image générée
        image_url = response.data[0].url
        
        return image_url
    except Exception as e:
        print(f"Erreur lors de la génération de l'image : {str(e)}")
        return None

def download_image(url, output_path):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Vérifie si la requête a réussi
        
        # Télécharger l'image
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"Image sauvegardée avec succès : {output_path}")
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors du téléchargement de l'image : {str(e)}")

def main():
    # Créer le répertoire de sortie s'il n'existe pas
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    # Lire le prompt pour l'image
    with open('output_text/image_prompt_1.txt', 'r', encoding='utf-8') as f:
        image_prompt = f.read().strip()

    # Générer l'image
    image_url = generate_image(image_prompt)

    if image_url:
        # Télécharger et sauvegarder l'image
        output_path = os.path.join(output_dir, "slide_1_image.png")
        download_image(image_url, output_path)

        print("Image générée et sauvegardée avec succès.")
    else:
        print("Échec de la génération de l'image.")

if __name__ == "__main__":
    main()