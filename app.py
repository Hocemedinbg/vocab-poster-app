import gradio as gr
import requests
import base64
import io
import os
import time
import zipfile
import tempfile
from PIL import Image

def generate_with_gemini(api_key, clothing_style, title_text, obj1, obj2, obj3, obj4, original_img):
    # 1. Convertir l'image en Base64 pour l'envoyer à Google
    buffered = io.BytesIO()
    original_img.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    # 2. Le prompt
    prompt = (
        f"Look at the provided image. It's a children's English vocabulary poster. "
        f"Generate a NEW image that looks EXACTLY like this one in terms of style, layout, and design. "
        f"Keep the top texts '@abcyarakidstv', 'Learn English' and 'VOCABULARY'. "
        f"Change the central large title to: '{title_text}'. "
        f"Change the cartoon girl's clothes to: {clothing_style}. "
        f"Change the 4 vocabulary items in the grid to these 4 new items: "
        f"1. {obj1}, 2. {obj2}, 3. {obj3}, 4. {obj4}. "
        f"Draw these 4 new items in the same cute cartoon style. "
        f"Return only the image."
    )
    
    # 3. L'URL directe de l'API REST de Google Gemini
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}"
    
    # 4. Le corps de la requête (format JSON)
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/png", "data": img_base64}}
            ]
        }],
        "generationConfig": {
            "responseModalities": ["IMAGE", "TEXT"]
        }
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        # 5. Envoi de la requête
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            # On cherche l'image dans la réponse
            for candidate in data.get('candidates', []):
                for part in candidate.get('content', {}).get('parts', []):
                    if 'inlineData' in part:
                        image_bytes = base64.b64decode(part['inlineData']['data'])
                        return Image.open(io.BytesIO(image_bytes))
            
            print("Réponse Gemini sans image:", data)
            return None
        else:
            print(f"Erreur API Gemini ({response.status_code}):", response.text)
            return None
            
    except Exception as e:
        print(f"Erreur réseau:", e)
        return None

def batch_generate_images(api_key, clothing_style, title_text, word_list, progress=gr.Progress()):
    if not api_key:
        yield [], "❌ Erreur: Tu dois renseigner ta clé API Gemini.", None
        return

    try:
        original_img = Image.open("original.png")
    except FileNotFoundError:
        yield [], "❌ Erreur: Le fichier original.png est introuvable.", None
        return

    raw_words = word_list.split('\n')
    ignore_words = ["winter adjectives", "winter clothes", "download"]
    words = [w.strip() for w in raw_words if w.strip() and w.strip().lower() not in ignore_words]
    
    chunks = [words[i:i + 4] for i in range(0, len(words), 4)]
    total_images = len(chunks)
    
    if total_images == 0:
        yield [], "❌ La liste est vide.", None
        return

    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "vocab_posters.zip")
    gallery_items = []
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for i, chunk in enumerate(chunks):
            while len(chunk) < 4:
                chunk.append("None")
            obj1, obj2, obj3, obj4 = chunk
            
            progress((i / total_images), desc=f"Génération image {i+1}/{total_images} avec Gemini...")

            img = generate_with_gemini(api_key, clothing_style, title_text, obj1, obj2, obj3, obj4, original_img)
            
            if img:
                img_name = f"poster_{i+1}_{obj1}_{obj2}.png".replace(" ", "_").replace("/", "_")
                img_path = os.path.join(temp_dir, img_name)
                img.save(img_path)
                zipf.write(img_path, arcname=img_name)
                gallery_items.append((img_path, f"Poster {i+1}: {obj1}, {obj2}, {obj3}, {obj4}"))
                yield gallery_items, f"✅ Image {i+1}/{total_images} générée !", None
            else:
                yield gallery_items, f"⚠️ L'image {i+1} n'a pas pu être générée. Regarde le terminal.", None
            
            time.sleep(2)

    progress(1.0, desc="Terminé ! ✅")
    yield gallery_items, f"🎉 Processus terminé ! Le ZIP est prêt !", zip_path


with gr.Blocks(title="Batch Vocab Poster Generator", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🎨 Batch Vocabulary Poster Generator (API REST Directe)")

    with gr.Row():
        with gr.Column(scale=1):
            api_key_input = gr.Textbox(label="🔑 Clé API Google Gemini", type="password", placeholder="AIza...")
            clothing_input = gr.Textbox(label="👗 Style de vêtements (fixe)", value="Winter outfit")
            title_input = gr.Textbox(label="🏷️ Titre central (fixe)", value="Winter Vocabulary")
            
            word_list_input = gr.Textbox(
                label="📝 Liste de mots (1 par ligne)", 
                lines=15, 
                value="""jumper
bitter
scarf
freezing
slushy
vest
drafty
beanie
cardigan
chilly
frozen
boots
gloves
earmuffs
wet
misty
Winter Adjectives
melting
fleece
trousers
slippery
jacket
raincoat
icy
hoodie
foggy
coat
cloudy
sweater
white
wellington boots
Winter Clothes
snowy
dreary
socks
Download
sparkling
stockings
cold
glittering
frosty"""
            )

            generate_btn = gr.Button("🚀 Générer le lot avec Gemini", variant="primary", size="lg")

        with gr.Column(scale=1):
            gr.Markdown("### 🖼️ Aperçu des posters générés")
            gallery_output = gr.Gallery(label="Galerie", columns=2, height=600, show_label=False)
            status_output = gr.Textbox(label="📊 Statut", interactive=False, lines=2)
            download_btn = gr.DownloadButton("📥 Télécharger le ZIP", variant="secondary", size="lg")

    generate_btn.click(
        fn=batch_generate_images,
        inputs=[api_key_input, clothing_input, title_input, word_list_input],
        outputs=[gallery_output, status_output, download_btn]
    )

if __name__ == "__main__":
    app.launch()
