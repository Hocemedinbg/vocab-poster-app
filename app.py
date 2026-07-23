import gradio as gr
import requests
from PIL import Image
from io import BytesIO
import urllib.parse
import random
import zipfile
import os
import tempfile
import time

def get_original_image_url():
    # 🔴 REMPLACE CECI AVEC TON PSEUDO ET TON REPO
    github_user = "TON_PSEUDO_GITHUB"
    repo_name = "vocab-poster-app"
    return f"https://raw.githubusercontent.com/{github_user}/{repo_name}/main/original.png"

def batch_generate_images(
    clothing_style, 
    title_text, 
    word_list, 
    model_choice, 
    use_img2img, 
    strength,
    progress=gr.Progress(track_tqdm=False)
):
    # ─── 1. Nettoyage et découpage de la liste ───
    raw_words = word_list.split('\n')
    
    # Petit filtre intelligent pour enlever les titres de catégories de ta liste
    ignore_words = ["winter adjectives", "winter clothes", "download"]
    words = [w.strip() for w in raw_words if w.strip() and w.strip().lower() not in ignore_words]
    
    # Découpage en groupes de 4
    chunks = [words[i:i + 4] for i in range(0, len(words), 4)]
    total_images = len(chunks)
    
    if total_images == 0:
        yield [], "❌ La liste est vide.", None
        return

    # ─── 2. Préparation du dossier temporaire et du ZIP ───
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "vocab_posters.zip")
    
    gallery_items = []
    
    # Création du fichier ZIP
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        
        # ─── 3. Boucle de génération par 4 ───
        for i, chunk in enumerate(chunks):
            # Si le dernier groupe n'a pas 4 mots, on complète par "None" pour ne pas planter
            while len(chunk) < 4:
                chunk.append("None")
            obj1, obj2, obj3, obj4 = chunk
            
            progress((i / total_images), desc=f"Génération image {i+1}/{total_images}...")

            # Construction du prompt
            prompt = (
                f"A children's English vocabulary learning poster, "
                f"flat vector illustration style with vibrant kid-friendly colors.\n\n"
                f"Poster layout:\n"
                f"- Top section with text '@abcyarakidstv' and 'Learn English'\n"
                f"- A 'VOCABULARY' section label\n"
                f"- Central large title: '{title_text}' in bold colorful playful letters\n"
                f"- A cute cartoon girl wearing {clothing_style}\n"
                f"- Four labeled vocabulary item illustrations in a 2x2 grid:\n"
                f"  1. {obj1}\n  2. {obj2}\n  3. {obj3}\n  4. {obj4}\n"
                f"- Colorful background with floating hearts, stars, and green leaves\n"
                f"- Educational poster design, clean modern illustration for children"
            )

            encoded_prompt = urllib.parse.quote(prompt)
            seed = random.randint(0, 999999)

            base_url = "https://image.pollinations.ai/prompt/"
            url = f"{base_url}{encoded_prompt}?width=1024&height=1024&model={model_choice}&nologo=true&seed={seed}"

            if use_img2img:
                ref_url = get_original_image_url()
                if "TON_PSEUDO_GITHUB" not in ref_url:
                    encoded_ref = urllib.parse.quote(ref_url, safe="")
                    url += f"&image={encoded_ref}&strength={strength}"

            # Appel API
            try:
                response = requests.get(url, timeout=180)
                if response.status_code == 200:
                    img = Image.open(BytesIO(response.content))
                    
                    # Sauvegarde locale temporaire
                    img_name = f"poster_{i+1}_{obj1}_{obj2}.png".replace(" ", "_").replace("/", "_")
                    img_path = os.path.join(temp_dir, img_name)
                    img.save(img_path)
                    
                    # Ajout au ZIP
                    zipf.write(img_path, arcname=img_name)
                    
                    # Ajout à la galerie (chemin, légende)
                    gallery_items.append((img_path, f"Poster {i+1}: {obj1}, {obj2}, {obj3}, {obj4}"))
                    
                    # Mise à jour de l'UI en temps réel (yield)
                    status_msg = f"✅ Image {i+1}/{total_images} générée !"
                    yield gallery_items, status_msg, None
                    
            except Exception as e:
                yield gallery_items, f"❌ Erreur sur l'image {i+1}: {str(e)}", None

    # ─── 4. Fin du processus ───
    progress(1.0, desc="Terminé ! ✅")
    final_status = f"🎉 Processus terminé ! {total_images} images générées et ajoutées au ZIP."
    yield gallery_items, final_status, zip_path


# ─── Interface Gradio ───
with gr.Blocks(title="Batch Vocab Poster Generator", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🎨 Batch Vocabulary Poster Generator\nGénère plusieurs posters en une seule fois et télécharge-les en ZIP !")

    with gr.Row():
        # COLONNE GAUCHE : Inputs
        with gr.Column(scale=1):
            clothing_input = gr.Textbox(label="👗 Style de vêtements (fixe)", value="Winter jacket")
            title_input = gr.Textbox(label="🏷️ Titre central (fixe)", value="Winter Time")
            
            word_list_input = gr.Textbox(
                label="📝 Liste de mots (1 par ligne)", 
                lines=15, 
                placeholder="Colle ta liste ici...",
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

            with gr.Accordion("⚙️ Paramètres avancés", open=False):
                model_choice = gr.Dropdown(choices=["flux", "turbo"], value="flux", label="🤖 Modèle IA")
                use_img2img = gr.Checkbox(label="🔗 Utiliser img2img", value=True)
                strength_slider = gr.Slider(minimum=0.1, maximum=1.0, value=0.7, step=0.1, label="💪 Force de modification")

            generate_btn = gr.Button("🚀 Générer le lot d'images", variant="primary", size="lg")

        # COLONNE DROITE : Outputs
        with gr.Column(scale=1):
            gr.Markdown("### 🖼️ Aperçu des posters générés")
            gallery_output = gr.Gallery(label="Galerie", columns=2, height=600, show_label=False)
            
            status_output = gr.Textbox(label="📊 Statut", interactive=False, lines=2)
            
            download_btn = gr.DownloadButton("📥 Télécharger le ZIP", variant="secondary", size="lg")

    # Connexion bouton -> fonction
    # On utilise yield, donc Gradio sait qu'on fait une fonction asynchrone
    generate_btn.click(
        fn=batch_generate_images,
        inputs=[clothing_input, title_input, word_list_input, model_choice, use_img2img, strength_slider],
        outputs=[gallery_output, status_output, download_btn]
    )

if __name__ == "__main__":
    app.launch()
