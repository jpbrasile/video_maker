import json
import os
from dotenv import load_dotenv
import anthropic
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip
from moviepy.editor import VideoFileClip, concatenate_videoclips, vfx
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
def extract_content(response):
    if isinstance(response, list) and len(response) > 0:
        return response[0].text if hasattr(response[0], 'text') else str(response[0])
    return str(response)
# Charger les variables d'environnement
load_dotenv()

# Récupérer les clés API
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialiser les clients
anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
openai_client = OpenAI(api_key=openai_api_key)

def get_slides_from_claude(content):
    prompt = f"""
    Transforme le texte suivant en une structure JSON de diapositives. Chaque diapositive doit avoir un numéro, un titre, un contenu principal, du code (si présent), et des instructions (si présentes). Voici le texte :

    {content}

    Réponds uniquement avec le JSON structuré, sans aucun texte supplémentaire.
    """

    message = anthropic_client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=4000,
        temperature=0,
        system="Tu es un assistant spécialisé dans la structuration de contenu pour des présentations.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return extract_content(message.content)

def create_html_slide(slide_data):
    titre = slide_data.get('titre', 'Titre non disponible')
    contenu = slide_data.get('contenu', 'Contenu non disponible')
    numero = slide_data.get('numero', '0')
    
    # Gestion du code
    code = slide_data.get('code', None)
    if code is True:
        code = "Code non fourni"
    elif isinstance(code, str):
        code = f"<pre><code>{code}</code></pre>"
    else:
        code = ""

    html_template = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{titre}</title>
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
                grid-template-rows: auto auto 1fr auto;
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
            pre {{
                background-color: #f4f4f4;
                border: 1px solid #ddd;
                border-left: 3px solid #f36d33;
                color: #666;
                page-break-inside: avoid;
                font-family: monospace;
                font-size: 15px;
                line-height: 1.6;
                margin-bottom: 1.6em;
                max-width: 100%;
                overflow: auto;
                padding: 1em 1.5em;
                display: block;
                word-wrap: break-word;
            }}
        </style>
    </head>
    <body>
        <div class="slide-container">
            <h1 class="slide-title">{titre}</h1>
            <div class="slide-image-container">
                <img class="slide-image" src="slide_{numero}_image.png" alt="Slide Image">
            </div>
            <p class="slide-content">{contenu}</p>
            {code}
        </div>
    </body>
    </html>
    """
    return html_template

def create_voice_over(slide_data):
    prompt = f"""
    Crée un texte de voice-over pour la diapositive suivante :
    Titre: {slide_data['titre']}
    Contenu: {slide_data['contenu']}
    
    Le texte doit être clair, concis et engageant pour une présentation orale.
    Commence directement par le contenu du voice-over, sans aucune introduction ou mention du fait que c'est un voice-over.
    Limite-toi à 2-3 phrases maximum.
    """
    response = anthropic_client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        temperature=0.7,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return extract_content(response.content)

def create_image_prompt(slide_data):
    prompt = f"""
    Crée un prompt pour générer une image qui illustre la diapositive suivante :
    Titre: {slide_data['titre']}
    Contenu: {slide_data['contenu']}
    
    Le prompt doit décrire une image pertinente et visuellement attrayante.
    """
    response = anthropic_client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        temperature=0.7,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return extract_content(response.content)

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

def text_to_speech(text, output_path):
    try:
        response = openai_client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        with open(output_path, 'wb') as file:
            file.write(response.content)
        print(f"Fichier audio créé avec succès : {output_path}")
    except Exception as e:
        print(f"Erreur lors de la création du fichier audio : {str(e)}")

def render_html_to_image(html_file, output_image):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--force-device-scale-factor=1")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    driver.get(f"file://{os.path.abspath(html_file)}")
    driver.set_window_size(1920, 1080)
    
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "slide-container"))
    )
    
    time.sleep(2)
    driver.save_screenshot(output_image)
    driver.quit()

def create_video_from_slide(html_file, audio_file, output_file, duration=None):
    temp_image = "output/temp_slide_image.png"
    render_html_to_image(html_file, temp_image)

    pil_image = Image.open(temp_image).convert('RGB')
    pil_image.save(temp_image)

    image_clip = ImageClip(temp_image)
    audio_clip = AudioFileClip(audio_file)

    if duration is None:
        duration = audio_clip.duration

    image_clip = image_clip.set_duration(duration)
    video_clip = CompositeVideoClip([image_clip]).set_audio(audio_clip)

    video_clip.write_videofile(output_file, fps=24)
    os.remove(temp_image)


def process_slide(slide_data, output_dir):
    print(f"Contenu de la diapositive {slide_data.get('numero', 'inconnue')}:")
    print(json.dumps(slide_data, indent=2, ensure_ascii=False))
    print("-" * 50)

    required_keys = ['numero', 'titre', 'contenu']
    for key in required_keys:
        if key not in slide_data:
            print(f"Avertissement : La clé '{key}' est manquante dans la diapositive {slide_data.get('numero', 'inconnue')}.")
            slide_data[key] = f"{key.capitalize()} non disponible"

    if 'code' in slide_data and slide_data['code'] is True:
        print(f"Avertissement : La diapositive {slide_data['numero']} a un indicateur de code mais pas de contenu de code.")
        slide_data['code'] = "Code non fourni"

    slide_number = slide_data['numero']
    # Créer le HTML
    html_content = create_html_slide(slide_data)
    html_file = os.path.join(output_dir, f"slide_{slide_number}.html")
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # Créer le voice-over
    voice_over = create_voice_over(slide_data)
    voice_over_file = os.path.join(output_dir, f"voice_over_{slide_number}.txt")
    with open(voice_over_file, 'w', encoding='utf-8') as f:
        f.write(voice_over)

    # Générer l'audio
    audio_file = os.path.join(output_dir, f"audio_{slide_number}.mp3")
    text_to_speech(voice_over, audio_file)

    # Générer l'image
    image_prompt = create_image_prompt(slide_data)
    image_url = generate_image(image_prompt)
    if image_url:
        image_file = os.path.join(output_dir, f"slide_{slide_number}_image.png")
        download_image(image_url, image_file)

    # Créer la vidéo
    video_file = os.path.join(output_dir, f"video_{slide_number}.mp4")
    create_video_from_slide(html_file, audio_file, video_file)

def aggregate_videos(output_dir, num_slides, transition_duration=1):
    video_clips = []
    for i in range(1, num_slides + 1):
        video_path = os.path.join(output_dir, f"video_{i}.mp4")
        if os.path.exists(video_path):
            clip = VideoFileClip(video_path)
            
            # Ajouter un fondu en entrée et en sortie
            clip = clip.fx(vfx.fadeout, duration=transition_duration/2)
            clip = clip.fx(vfx.fadein, duration=transition_duration/2)
            
            # Ajouter un blanc à la fin de l'audio si nécessaire
            audio_duration = clip.audio.duration if clip.audio else 0
            if audio_duration < clip.duration:
                clip = clip.set_audio(clip.audio.set_duration(clip.duration))
            
            video_clips.append(clip)
        else:
            print(f"Avertissement : La vidéo {video_path} n'existe pas.")

    # Créer la vidéo finale avec des transitions
    final_clip = concatenate_videoclips(video_clips, method="compose")
    
    # Exporter la vidéo finale
    final_output = os.path.join(output_dir, "final_video.mp4")
    final_clip.write_videofile(final_output, fps=24)
    
    # Fermer les clips pour libérer les ressources
    for clip in video_clips:
        clip.close()
    final_clip.close()

    print(f"Vidéo finale créée : {final_output}")

# def main():
#     output_dir = "output"
#     os.makedirs(output_dir, exist_ok=True)

#     # Lire le contenu du fichier
#     with open('PLACEHOLDER_TEXTE_VIDEO.txt', 'r', encoding='utf-8') as file:
#         content = file.read()
#     print("Contenu du fichier lu avec succès.")

#     # Obtenir le JSON structuré de Claude
#     json_content = get_slides_from_claude(content)
#     print("JSON obtenu de Claude.")

#     # Nettoyer le JSON
#     json_content = json_content.replace("```json", "").replace("```", "").strip()

#     # Parser le JSON
#     try:
#         slides_data = json.loads(json_content)
#         print(f"JSON parsé avec succès. Nombre total de diapositives : {len(slides_data)}")
#     except json.JSONDecodeError as e:
#         print(f"Erreur lors du parsing JSON : {e}")
#         print("Contenu JSON problématique:")
#         print(json_content)
#         return

#     # Écrire le JSON dans un fichier
#     with open('slides_data.json', 'w', encoding='utf-8') as json_file:
#         json.dump(slides_data, json_file, ensure_ascii=False, indent=2)
#     print("Fichier JSON sauvegardé : slides_data.json")

#     # Traiter uniquement la diapositive 5 (index 4 car les listes commencent à 0)
#     if len(slides_data) >= 6:
#         print(f"Traitement de la diapositive 5...")
#         process_slide(slides_data[5], output_dir)
#     else:
#         print("La diapositive 5 n'existe pas dans les données.")

#     print("Traitement terminé.")

# if __name__ == "__main__":
#     main()

def main():
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    # Lire le contenu du fichier
    try:
        with open('PLACE_HOLDER_TEXTE_VIDEO.txt', 'r', encoding='utf-8') as file:
            content = file.read()
        print("Contenu du fichier PLACE_HOLDER_TEXTE_VIDEO.txt lu avec succès.")
    except FileNotFoundError:
        print("Erreur : Le fichier PLACE_HOLDER_TEXTE_VIDEO.txt n'a pas été trouvé.")
        return
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier : {str(e)}")
        return

    # Obtenir le JSON structuré de Claude
    json_content = get_slides_from_claude(content)
    print("JSON obtenu de Claude.")

    # Nettoyer le JSON
    json_content = json_content.replace("```json", "").replace("```", "").strip()

    # Parser le JSON
    try:
        slides_data = json.loads(json_content)
        print(f"JSON parsé avec succès. Nombre de diapositives : {len(slides_data)}")
    except json.JSONDecodeError as e:
        print(f"Erreur lors du parsing JSON : {e}")
        print("Contenu JSON problématique:")
        print(json_content)
        return

    # Écrire le JSON dans un fichier
    with open('slides_data.json', 'w', encoding='utf-8') as json_file:
        json.dump(slides_data, json_file, ensure_ascii=False, indent=2)
    print("Fichier JSON sauvegardé : slides_data.json")

    # Traiter chaque diapositive
    for slide in slides_data:
        print(f"Traitement de la diapositive {slide['numero']}...")
        process_slide(slide, output_dir)

    print("Traitement de toutes les diapositives terminé.")

    # Agréger les vidéos
    print("Agrégation des vidéos...")
    aggregate_videos(output_dir, len(slides_data))

    print("Processus complet terminé.")

if __name__ == "__main__":
    main()