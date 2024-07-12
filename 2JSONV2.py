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

def read_story_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            story_data = json.load(file)
        print(f"Contenu du fichier {file_path} lu avec succès.")
        return story_data
    except FileNotFoundError:
        print(f"Erreur : Le fichier {file_path} n'a pas été trouvé.")
        return None
    except json.JSONDecodeError as e:
        print(f"Erreur lors du parsing JSON : {e}")
        return None
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier : {str(e)}")
        return None

def process_story_slide(slide_data, output_dir):
    print(f"Traitement de la diapositive {slide_data.get('id', 'inconnue')}:")
    print(json.dumps(slide_data, indent=2, ensure_ascii=False))
    print("-" * 50)

    slide_number = slide_data['id']
    
    try:
        # Générer l'image
        image_prompt = slide_data['imagePrompt']
        image_url = generate_image(image_prompt)
        image_file = os.path.join(output_dir, f"story_slide_{slide_number}_image.png")
        if image_url:
            download_image(image_url, image_file)
        else:
            print(f"Avertissement : Impossible de générer l'image pour la diapositive {slide_number}")

        # Vérifier si l'image existe
        image_exists = os.path.exists(image_file)
        if not image_exists:
            print(f"Avertissement : L'image pour la diapositive {slide_number} n'existe pas")

        # Créer le HTML
        html_content = create_html_slide({
            'number': slide_number,
            'title': f"Slide {slide_number}",
            'description': slide_data['voiceOver']
        }, output_dir, image_exists, f"story_slide_{slide_number}_image.png")
        html_file = os.path.join(output_dir, f"story_slide_{slide_number}.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Créer le voice-over
        voice_over = slide_data['voiceOver']
        voice_over_file = os.path.join(output_dir, f"story_voice_over_{slide_number}.txt")
        with open(voice_over_file, 'w', encoding='utf-8') as f:
            f.write(voice_over)

        # Générer l'audio
        audio_file = os.path.join(output_dir, f"story_audio_{slide_number}.mp3")
        text_to_speech(voice_over, audio_file)

        # Créer la vidéo
        video_file = os.path.join(output_dir, f"story_video_{slide_number}.mp4")
        create_video_from_slide(html_file, audio_file, video_file)
        
        print(f"Traitement de la diapositive {slide_number} terminé avec succès.")
    except Exception as e:
        print(f"Erreur lors du traitement de la diapositive {slide_number}: {str(e)}")

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
    Transforme le texte suivant en une structure JSON de diapositives. Chaque diapositive doit avoir les propriétés suivantes :
    
    1. "number": Un numéro de diapositive (commençant à 1)
    2. "title": Le titre de la diapositive
    3. "description": Le contenu principal de la diapositive, formaté en HTML. Utilise des balises <p> pour les paragraphes et des balises <span class="highlight"> pour mettre en évidence les termes importants.
    4. "code": Du code (si présent), sans formatage particulier. Omets cette propriété s'il n'y a pas de code.
    5. "image_url": Une URL d'image fictive (par exemple, "https://example.com/path/to/image.png")

    Règles importantes :
    - Assure-toi que le JSON est valide et correctement formaté.
    - Utilise des doubles guillemets pour les chaînes de caractères dans le JSON.
    - Échappe correctement les guillemets et les caractères spéciaux dans les chaînes de caractères.
    - Pour le code, utilise \\n pour les sauts de ligne.
    - Limite chaque diapositive à un seul concept ou idée principale.
    - Crée autant de diapositives que nécessaire pour couvrir tout le contenu fourni.
    - N'inclus pas de propriétés vides ou nulles dans le JSON.

    Voici le texte à transformer :

    {content}

    Réponds uniquement avec le JSON structuré, sans aucun texte supplémentaire.
    """

    message = anthropic_client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=4000,
        temperature=0,
        system="Tu es un assistant spécialisé dans la structuration de contenu pour des présentations. Tu génères uniquement du JSON valide et bien formaté.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return extract_content(message.content)

def create_html_slide(slide_data, output_dir, image_exists, image_filename=None):
    title = slide_data.get('title', 'Titre non disponible')
    description = slide_data.get('description', 'Contenu non disponible')
    code = slide_data.get('code', '')
    slide_number = slide_data.get('number', '0')
    
    image_path = image_filename if image_exists and image_filename else f"slide_{slide_number}_image.png"
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        <style>
            body, html {{
                font-family: 'Arial', sans-serif;
                margin: 0;
                padding: 0;
                height: 100vh;
                width: 100vw;
                background-color: #333333;
                color: #ffffff;
                overflow: hidden;
            }}
            .container {{
                display: flex;
                width: 100%;
                height: 100%;
            }}
            .text-container {{
                flex: 1;
                padding: 40px;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }}
            .title {{
                font-size: 3em;
                font-weight: bold;
                margin-bottom: 30px;
                color: #FFD700;
            }}
            .content {{
                flex-grow: 1;
                display: flex;
                flex-direction: column;
            }}
            .description {{
                font-size: 1.5em;
                line-height: 1.6;
                margin-bottom: 20px;
            }}
            .highlight {{
                color: #4CAF50;
                font-weight: bold;
            }}
            .code-container {{
                background-color: #1E1E1E;
                border-radius: 5px;
                padding: 20px;
                margin-top: 20px;
                overflow: hidden;
            }}
            pre {{
                margin: 0;
            }}
            code {{
                font-family: 'Courier New', monospace;
                color: #E0E0E0;
                white-space: pre-wrap;
                word-break: break-all;
            }}
            .image-container {{
                flex: 1;
                display: flex;
                align-items: center;
                justify-content: center;
                background-color: #4a4a4a;
                padding: 20px;
            }}
            img {{
                max-width: 100%;
                max-height: 100%;
                object-fit: contain;
                border-radius: 10px;
                box-shadow: 0 0 20px rgba(0, 0, 0, 0.3);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="text-container">
                <h1 class="title">{title}</h1>
                <div class="content">
                    <div class="description">{description}</div>
                    {f'<div class="code-container"><pre><code>{code}</code></pre></div>' if code else ''}
                </div>
            </div>
            <div class="image-container">
                {f'<img src="{image_path}" alt="Slide Image">' if image_exists else ''}
            </div>
        </div>
        <script>
            function adjustTextSize() {{
                const textContainer = document.querySelector('.text-container');
                const title = document.querySelector('.title');
                const description = document.querySelector('.description');
                const codeContainers = document.querySelectorAll('.code-container');
                
                const maxTitleSize = 3;
                const minTitleSize = 1.5;
                const maxDescSize = 1.5;
                const minDescSize = 0.8;
                
                let titleSize = maxTitleSize;
                let descSize = maxDescSize;
                
                function setFontSizes(tSize, dSize) {{
                    title.style.fontSize = `${{tSize}}em`;
                    description.style.fontSize = `${{dSize}}em`;
                    codeContainers.forEach(container => {{
                        const code = container.querySelector('code');
                        code.style.fontSize = `${{dSize * 0.9}}em`;
                    }});
                }}
                
                function isOverflowing() {{
                    return textContainer.scrollHeight > textContainer.clientHeight;
                }}
                
                // Binary search for the best fit
                while (titleSize > minTitleSize || descSize > minDescSize) {{
                    setFontSizes(titleSize, descSize);
                    
                    if (isOverflowing()) {{
                        titleSize = Math.max(titleSize - 0.1, minTitleSize);
                        descSize = Math.max(descSize - 0.1, minDescSize);
                    }} else {{
                        break;
                    }}
                }}
                
                // If still overflowing, truncate description
                if (isOverflowing()) {{
                    const words = description.innerHTML.split(' ');
                    while (words.length > 1 && isOverflowing()) {{
                        words.pop();
                        description.innerHTML = words.join(' ') + '...';
                    }}
                }}
            }}
            
            window.onload = adjustTextSize;
            window.onresize = adjustTextSize;
        </script>
    </body>
    </html>
    """
    return html_template
def render_html_to_image(html_file, output_image):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--force-device-scale-factor=1")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        driver.get(f"file://{os.path.abspath(html_file)}")
        driver.set_window_size(1920, 1080)
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "container"))
        )
        
        time.sleep(2)
        driver.save_screenshot(output_image)
    except Exception as e:
        print(f"Erreur lors du rendu HTML en image : {str(e)}")
    finally:
        driver.quit()
def process_slide(slide_data, output_dir):
    print(f"Traitement de la diapositive {slide_data.get('number', 'inconnue')}:")
    print(json.dumps(slide_data, indent=2, ensure_ascii=False))
    print("-" * 50)

    required_keys = ['number', 'title', 'description']
    for key in required_keys:
        if key not in slide_data:
            print(f"Avertissement : La clé '{key}' est manquante dans la diapositive {slide_data.get('number', 'inconnue')}.")
            slide_data[key] = f"{key.capitalize()} non disponible"

    slide_number = slide_data['number']
    
    try:
        # Générer l'image
        image_prompt = create_image_prompt(slide_data)
        image_url = generate_image(image_prompt)
        image_file = os.path.join(output_dir, f"slide_{slide_number}_image.png")
        if image_url:
            download_image(image_url, image_file)
        else:
            print(f"Avertissement : Impossible de générer l'image pour la diapositive {slide_number}")

        # Vérifier si l'image existe
        image_exists = os.path.exists(image_file)
        if not image_exists:
            print(f"Avertissement : L'image pour la diapositive {slide_number} n'existe pas")

        # Créer le HTML après la génération de l'image
        html_content = create_html_slide(slide_data, output_dir, image_exists, f"slide_{slide_number}_image.png")
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

        # Créer la vidéo
        video_file = os.path.join(output_dir, f"video_{slide_number}.mp4")
        create_video_from_slide(html_file, audio_file, video_file)
        
        print(f"Traitement de la diapositive {slide_number} terminé avec succès.")
    except Exception as e:
        print(f"Erreur lors du traitement de la diapositive {slide_number}: {str(e)}")


def create_voice_over(slide_data):
    title = slide_data.get('title', 'Titre non disponible')
    description = slide_data.get('description', 'Description non disponible')
    
    # Supprimer les balises HTML de la description
    description = BeautifulSoup(description, "html.parser").get_text()
    
    prompt = f"""
    Créez un bref texte de voice-over pour la diapositive suivante, en vous concentrant sur les points clés :

    Titre : {title}
    Description : {description}

    Instructions :
    1. Commencez directement par le contenu principal, sans phrase d'introduction.
    2. Résumez les informations essentielles en 2-3 phrases concises.
    3. Utilisez un ton informatif et engageant.
    4. Évitez les détails techniques spécifiques comme les commandes exactes.
    5. Concentrez-vous sur l'objectif et les options disponibles plutôt que sur les détails d'implémentation.

    Votre réponse doit contenir uniquement le texte du voice-over, sans aucun texte supplémentaire.
    """
    
    try:
        response = anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            temperature=0.7,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return extract_content(response.content)
    except Exception as e:
        print(f"Erreur lors de la création du voice-over : {str(e)}")
        return f"Voice-over pour la diapositive : {title}"
    

def create_image_prompt(slide_data):
    image_description = slide_data.get('image_description', '')
    if not image_description:
        image_description = f"Une image illustrant le concept de {slide_data['title']}"
    
    prompt = f"""
    Crée un prompt pour générer une image qui illustre la diapositive suivante :
    Titre: {slide_data['title']}
    Description de l'image: {image_description}
    
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



def aggregate_videos(output_dir, num_slides, prefix="", transition_duration=1):
    video_clips = []
    for i in range(1, num_slides + 1):
        video_path = os.path.join(output_dir, f"{prefix}video_{i}.mp4")
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
    final_output = os.path.join(output_dir, f"{prefix}final_video.mp4")
    final_clip.write_videofile(final_output, fps=24)
    
    #Fermer les clips pour libérer les ressources
    for clip in video_clips:
        clip.close()
    final_clip.close()

    print(f"Vidéo finale créée : {final_output}")

def main():
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    # Demander à l'utilisateur de choisir le mode
    mode = input("Choisissez le mode (1: PLACE_HOLDER_TEXTE_VIDEO.txt, 2: story.json, 3: Test local) : ").strip()

    if mode == "1":
        # Mode PLACE_HOLDER_TEXTE_VIDEO.txt (fonctionnement actuel)
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

        process_func = process_slide

    elif mode == "2":
        # Mode story.json
        story_data = read_story_json('story.json')
        if story_data is None:
            return
        slides_data = story_data['story']
        process_func = process_story_slide

    elif mode == "3":
        # Mode test local
        slides_data = [
            {
                "number": 1,
                "title": "Diapositive de test",
                "description": "Ceci est une diapositive de test pour le mode local.",
                "image_url": "https://example.com/test_image.jpg"
            }
        ]
        process_func = process_slide
    else:
        print("Mode non valide. Fin du programme.")
        return

    # Demander à l'utilisateur s'il veut traiter une seule diapositive ou toutes
    test_mode = input("Voulez-vous traiter une seule diapositive ? (O/N) : ").strip().lower()

    # Fonction de remplacement pour le mode test
    def mock_generate_image(prompt):
        return "https://via.placeholder.com/1024x1024.png?text=Image+de+test"

    def mock_text_to_speech(text, output_path):
        with open(output_path, 'w') as f:
            f.write("Ceci est un fichier audio de test")
        print(f"Fichier audio de test créé : {output_path}")

    # Remplacer les fonctions réelles par les mocks en mode test
    if mode == "3":
        global generate_image, text_to_speech
        generate_image = mock_generate_image
        text_to_speech = mock_text_to_speech

    if test_mode == 'o':
        slide_number = int(input("Entrez le numéro de la diapositive à traiter : ")) - 1
        if 0 <= slide_number < len(slides_data):
            print(f"Traitement de la diapositive {slide_number + 1}...")
            process_func(slides_data[slide_number], output_dir)
        else:
            print(f"Aucune diapositive trouvée avec le numéro {slide_number + 1}")
    else:
        # Traiter chaque diapositive
        for i, slide in enumerate(slides_data, 1):
            print(f"Traitement de la diapositive {i}...")
            process_func(slide, output_dir)

        print("Traitement de toutes les diapositives terminé.")

        # Agréger les vidéos
        print("Agrégation des vidéos...")
        aggregate_videos(output_dir, len(slides_data), "story_" if mode == "2" else "")

    print("Processus complet terminé.")

if __name__ == "__main__":
    main()
