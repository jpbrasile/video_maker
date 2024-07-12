import os
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def render_html_to_image(html_file, output_image):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--force-device-scale-factor=1")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    driver.get(f"file://{os.path.abspath(html_file)}")
    
    # Définir la taille de la fenêtre à 1920x1080 (16:9)
    driver.set_window_size(1920, 1080)
    
    # Attendre que la page soit complètement chargée
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "slide-container"))
    )
    
    # Attendre un peu plus pour s'assurer que tout est rendu
    time.sleep(2)
    
    # Prendre une capture d'écran
    driver.save_screenshot(output_image)
    
    driver.quit()

def create_video_from_slide(html_file, audio_file, output_file, duration=None):
    # Rendre le HTML en image
    temp_image = "output/temp_slide_image.png"
    render_html_to_image(html_file, temp_image)

    # Charger l'image avec PIL et la convertir en mode RGB
    pil_image = Image.open(temp_image).convert('RGB')
    pil_image.save(temp_image)

    # Charger l'image avec MoviePy
    image_clip = ImageClip(temp_image)

    # Charger l'audio
    audio_clip = AudioFileClip(audio_file)

    # Si la durée n'est pas spécifiée, utiliser la durée de l'audio
    if duration is None:
        duration = audio_clip.duration

    # Définir la durée de l'image
    image_clip = image_clip.set_duration(duration)

    # Combiner l'image et l'audio
    video_clip = CompositeVideoClip([image_clip]).set_audio(audio_clip)

    # Écrire la vidéo
    video_clip.write_videofile(output_file, fps=24)

    # Supprimer l'image temporaire
    os.remove(temp_image)

def main():
    html_file = "output/slide_1.html"
    audio_file = "output/audio_1.mp3"
    output_file = "output/video_1.mp4"

    if not os.path.exists(html_file):
        print(f"Erreur : Le fichier HTML {html_file} n'existe pas.")
        return

    if not os.path.exists(audio_file):
        print(f"Erreur : Le fichier audio {audio_file} n'existe pas.")
        return

    try:
        create_video_from_slide(html_file, audio_file, output_file)
        print(f"Vidéo créée avec succès : {output_file}")
    except Exception as e:
        print(f"Erreur lors de la création de la vidéo : {str(e)}")

if __name__ == "__main__":
    main()