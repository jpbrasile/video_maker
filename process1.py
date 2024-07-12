import json
import os
from dotenv import load_dotenv
import anthropic

# Charger les variables d'environnement
load_dotenv()

# Récupérer la clé API depuis les variables d'environnement
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

# Initialiser le client Anthropic
client = anthropic.Anthropic(api_key=anthropic_api_key)

def get_claude_response(prompt):
    message = client.messages.create(
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
        return response[0].text
    return response

def create_html_slide(slide_data):
    prompt = f"""
    Crée une page HTML responsive pour la diapositive suivante :
    Titre: {slide_data['titre']}
    Contenu: {slide_data['contenu']}
    
    Inclus un espace pour une image avec l'id 'slide-image'.
    Utilise des styles CSS modernes et attrayants.
    """
    return get_claude_response(prompt)

def create_voice_over(slide_data):
    prompt = f"""
    Crée un texte de voice-over pour la diapositive suivante :
    Titre: {slide_data['titre']}
    Contenu: {slide_data['contenu']}
    
    Le texte doit être clair, concis et engageant pour une présentation orale.
    """
    return get_claude_response(prompt)

def create_image_prompt(slide_data):
    prompt = f"""
    Crée un prompt pour générer une image qui illustre la diapositive suivante :
    Titre: {slide_data['titre']}
    Contenu: {slide_data['contenu']}
    
    Le prompt doit décrire une image pertinente et visuellement attrayante.
    """
    return get_claude_response(prompt)

def main():
    # Créer le répertoire de sortie s'il n'existe pas
    output_dir = "output_text"
    os.makedirs(output_dir, exist_ok=True)

    # Lire le fichier JSON des diapositives
    with open('slides_data.json', 'r', encoding='utf-8') as f:
        slides_data = json.load(f)

    # Traiter la première diapositive
    first_slide = slides_data[0]

    # Créer la planche HTML
    html_content = create_html_slide(first_slide)
    with open(os.path.join(output_dir, "slide_1.html"), "w", encoding='utf-8') as f:
        f.write(html_content)

    # Créer le voice over
    voice_over = create_voice_over(first_slide)
    with open(os.path.join(output_dir, "voice_over_1.txt"), "w", encoding='utf-8') as f:
        f.write(voice_over)

    # Créer le prompt pour l'image
    image_prompt = create_image_prompt(first_slide)
    with open(os.path.join(output_dir, "image_prompt_1.txt"), "w", encoding='utf-8') as f:
        f.write(image_prompt)

    print("Traitement de la première diapositive terminé. Fichiers créés dans le répertoire 'output_text'.")

if __name__ == "__main__":
    main()