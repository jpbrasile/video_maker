import json
import os
import requests
from dotenv import load_dotenv
import anthropic
from openai import OpenAI
from bs4 import BeautifulSoup

# Charger les variables d'environnement
load_dotenv()

# Récupérer les clés API
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialiser les clients
anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
openai_client = OpenAI(api_key=openai_api_key)

def get_claude_response(prompt):
    message = anthropic_client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        temperature=0.7,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return extract_content(message.content)

def extract_content(response):
    if isinstance(response, list) and len(response) > 0:
        return response[0].text if hasattr(response[0], 'text') else str(response[0])
    return str(response)

def create_html_slide(slide_data):
    html_template = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{slide_data['titre']}</title>
        <style>
            body, html {{
                height: 100%;
                margin: 0;
                padding: 0;
                overflow: hidden;
                font-family: Arial, sans-serif;
            }}
            .slide-container {{
                display: grid;
                grid-template-rows: auto 1fr auto;
                height: 100vh;
                padding: 2vh;
                box-sizing: border-box;
            }}
            .slide-title {{
                font-size: 5vh;
                text-align: center;
                margin-bottom: 2vh;
            }}
            .slide-image-container {{
                display: flex;
                justify-content: center;
                align-items: center;
                overflow: hidden;
            }}
            .slide-image {{
                max-width: 100%;
                max-height: 100%;
                object-fit: contain;
            }}
            .slide-content {{
                font-size: 3vh;
                text-align: center;
                margin-top: 2vh;
            }}
        </style>
    </head>
    <body>
        <div class="slide-container">
            <h1 class="slide-title">{slide_data['titre']}</h1>
            <div class="slide-image-container">
                <img class="slide-image" src="slide_1_image.png" alt="Slide Image">
            </div>
            <p class="slide-content">{slide_data['contenu']}</p>
        </div>
    </body>
    </html>
    """
    return html_template
def ensure_overflow_hidden(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    body = soup.find('body')
    if body:
        current_style = body.get('style', '')
        if 'overflow: hidden;' not in current_style:
            body['style'] = f"{current_style}; overflow: hidden;"
    return str(soup)

def create_voice_over(slide_data):
    prompt = f"""
    Crée un texte de voice-over pour la diapositive suivante :
    Titre: {slide_data['titre']}
    Contenu: {slide_data['contenu']}
    
    Le texte doit être clair, concis et engageant pour une présentation orale.
    Commence directement par le contenu du voice-over, sans aucune introduction ou mention du fait que c'est un voice-over.
    Limite-toi à 2-3 phrases maximum.
    """
    return get_claude_response(prompt)

def text_to_speech(text, output_path):
    try:
        response = openai_client.audio.speech.create(
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
def create_image_prompt(slide_data):
    prompt = f"""
    Crée un prompt pour générer une image qui illustre la diapositive suivante :
    Titre: {slide_data['titre']}
    Contenu: {slide_data['contenu']}
    
    Le prompt doit décrire une image pertinente et visuellement attrayante.
    """
    return get_claude_response(prompt)

def generate_image(prompt):
    try:
        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        print(f"Erreur lors de la génération de l'image : {str(e)}")
        return None

def download_image(url, output_path):
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"Image sauvegardée avec succès : {output_path}")
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors du téléchargement de l'image : {str(e)}")

def insert_image_into_html(html_content, image_path):
    soup = BeautifulSoup(html_content, 'html.parser')
    img_placeholder = soup.find(id='slide-image')
    if img_placeholder:
        img_tag = soup.new_tag('img', src=image_path, alt="Slide Image")
        img_tag['class'] = 'slide-image'
        img_placeholder.replace_with(img_tag)
    return str(soup)

from bs4 import BeautifulSoup


def validate_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    is_valid = True
    messages = []

    if not soup.find('html'):
        is_valid = False
        messages.append("Balise <html> manquante")
    if not soup.find('head'):
        is_valid = False
        messages.append("Balise <head> manquante")
    if not soup.find('body'):
        is_valid = False
        messages.append("Balise <body> manquante")
    if not soup.find(id='slide-image'):
        is_valid = False
        messages.append("Élément avec id 'slide-image' manquant")
    
    body = soup.find('body')
    if body and 'overflow: hidden' not in body.get('style', ''):
        is_valid = False
        messages.append("Le style 'overflow: hidden;' est manquant sur le body")
    
    return is_valid, str(soup), messages
    

def main():
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    # Lire le fichier JSON des diapositives
    with open('slides_data.json', 'r', encoding='utf-8') as f:
        slides_data = json.load(f)

    # Traiter la première diapositive
    first_slide = slides_data[0]

    # Créer la planche HTML
    html_content = create_html_slide(first_slide)
    
    try:
        is_valid, validated_html, messages = validate_html(html_content)
        if not is_valid:
            print("Avertissements dans le HTML généré :")
            for message in messages:
                print(f"- {message}")
        final_html = ensure_overflow_hidden(validated_html)
    except Exception as e:
        print(f"Erreur lors de la validation du HTML : {e}")
        final_html = html_content  # Utiliser le HTML non validé en cas d'erreur
    
    # Sauvegarder le HTML brut pour inspection
    with open(os.path.join(output_dir, "raw_slide_1.html"), "w", encoding='utf-8') as f:
        f.write(final_html)
    print(f"HTML brut sauvegardé dans {os.path.join(output_dir, 'raw_slide_1.html')}")

    # Créer le voice over
    voice_over = create_voice_over(first_slide)
    with open(os.path.join(output_dir, "voice_over_1.txt"), "w", encoding='utf-8') as f:
        f.write(voice_over)

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


    # Créer le prompt pour l'image et générer l'image
    image_prompt = create_image_prompt(first_slide)
    image_url = generate_image(image_prompt)

    if image_url:
        image_path = os.path.join(output_dir, "slide_1_image.png")
        download_image(image_url, image_path)
        print(f"Image sauvegardée : {image_path}")
        
        # Insérer l'image dans le HTML
        html_with_image = insert_image_into_html(final_html, "slide_1_image.png")
        
        # Sauvegarder le HTML final
        with open(os.path.join(output_dir, "slide_1.html"), "w", encoding='utf-8') as f:
            f.write(html_with_image)

        print("Traitement de la première diapositive terminé. Fichiers créés dans le répertoire 'output'.")
    else:
        print("Échec de la génération de l'image.")

if __name__ == "__main__":
    main()