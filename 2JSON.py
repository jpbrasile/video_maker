import json
import re

def parse_content(content):
    slides = []
    slide_pattern = r'\d+\.\s+(.*?)(?=\n\d+\.|\Z)'
    slides_raw = re.findall(slide_pattern, content, re.DOTALL)

    for index, slide_content in enumerate(slides_raw, start=1):
        slide = {
            "number": index,
            "title": "",
            "content": "",
            "code": None,
            "instructions": None
        }

        lines = slide_content.strip().split('\n')
        slide["title"] = lines[0].strip()

        content_lines = []
        code_lines = []
        in_code_block = False

        for line in lines[1:]:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                code_lines.append(line)
            else:
                content_lines.append(line)

        slide["content"] = '\n'.join(content_lines).strip()
        if code_lines:
            slide["code"] = '\n'.join(code_lines).strip()

        slides.append(slide)

    return slides

def main():
    try:
        with open('PLACEHOLDER_TEXTE_VIDEO.txt', 'r', encoding='utf-8') as file:
            content = file.read()

        slides = parse_content(content)
        output = {"slides": slides}

        with open('slides_data.json', 'w', encoding='utf-8') as json_file:
            json.dump(output, json_file, ensure_ascii=False, indent=2)

        print("Le fichier JSON a été généré avec succès : slides_data.json")
    except FileNotFoundError:
        print("Erreur : Le fichier PLACEHOLDER_TEXTE_VIDEO.txt n'a pas été trouvé.")
    except json.JSONDecodeError:
        print("Erreur : Problème lors de la création du JSON.")
    except Exception as e:
        print(f"Une erreur inattendue s'est produite : {str(e)}")

if __name__ == "__main__":
    main()