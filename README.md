## Faisons le tutoriel correspondant sous forme de vidéo
- L'idée est de partir de la synthèse récapitulée par sonnet 3.5 de notre programme précédent pour en faire un tuto.
- Pour cela on établit un dialogue avec sonnet 3.5 pour dégrossir le problème:
   -  Pour créer les planches HTML support,
    - Le texte des voice over,
    - Le prompt pour produire les images
    - Le code python pour stocker ces données dans des répertoires
    - Le code python créant les MP3 et les images et qui les stockent
    - Le code python qui fait l'assemblage
    - Ce dégrossissage montre qu'il est préférable d'avancer pas à pas en construisant et validant pas à pas le code python correspondant, ce que nous allons faire maintenant avec un nouveau thread sonnet 3.5.
  - Créer un code python permettant de dialoguer avec sonnet 3.5
      - On utilisera Visual Studio Code pour la mise en oeuvre et pour tester les codes
      - On utilisera anaconda pour créer un environnement logiciel spécifique. Nous utiliserons l'environnement teambot déjà créer avec conda activate teambot dans un terminal
      - On crée un répertoire de travail video-maker dans lequel on met le fichier .env avec nos clefs API, ainsi que les fichiers requirements.txt et anthropic-api-hello-world.py créer par sonnet 3.5
    Le dialogue fonctionne :

```
(base) PS C:\Users\test\Documents\AI_Automation\video_maker> conda activate teambot
(teambot) PS C:\Users\test\Documents\AI_Automation\video_maker> python anthropic-api-hello-world.py
```
- Claude dit: [TextBlock(text='Bonjour !', type='text')]
- Création d'une vidéo à partir d'un texte
- Ce projet automatise la création de vidéos éducatives à partir de contenu textuel, utilisant diverses technologies et APIs. Le processus se déroule en plusieurs étapes intégrées dans un script Python unique :
- Conversion du texte :
  - Lit le contenu du fichier PLACE_HOLDER_TEXTE_VIDEO.txt.
  - Utilise l'API Claude d'Anthropic pour convertir le texte en structure JSON de diapositives.
-Traitement des diapositives :
  - Génère un fichier HTML structuré avec CSS intégré pour chaque diapositive.
  - Crée un texte de voix off avec Claude.
  - Produit une image illustrative via l'API DALL-E d'OpenAI.
  - Génère un fichier audio de la voix off avec l'API Text-to-Speech d'OpenAI.
- Création des vidéos :
  - Capture une image du HTML rendu avec Selenium.
  - Combine l'image et l'audio en utilisant MoviePy pour chaque diapositive.
- Agrégation finale :
  - Assemble toutes les vidéos individuelles en une seule vidéo.
  - Ajoute des transitions entre les diapositives.
Le projet utilise Python avec diverses bibliothèques (BeautifulSoup, Requests, Pillow, MoviePy) et APIs (Anthropic, OpenAI).
Cette approche intégrée offre une solution complète et efficace pour la production automatisée de contenu vidéo éducatif, de la conversion du texte à la création de la vidéo finale.
⚙️ : Text to video de longue durée en open source
