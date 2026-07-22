import gradio as gr
import requests
from PIL import Image
from io import BytesIO
import urllib.parse
import random


def get_original_image_url():
    """
    Sur GitHub, on utilise les 'Raw URLs' pour récupérer les fichiers statiques.
    """
    # 🔴 REMPLACE CECI AVEC TON PSEUDO ET TON REPO
    github_user = "Hocemedinbg"
    repo_name = "vocab-poster-app"
    return f"https://raw.githubusercontent.com/{github_user}/{repo_name}/main/original.png"


def modify_image(
    clothing_style, title_text, obj1, obj2, obj3, obj4,
    model_choice, seed, use_img2img, strength,
    progress=gr.Progress()
):
    # ─── 1. Construction du prompt ───
    progress(0.1, desc="Construction du prompt...")

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

    if seed == -1:
        seed = random.randint(0, 999999)

    # ─── 2. Construction de l'URL Pollinations ───
    progress(0.2, desc="Préparation de la requête...")

    base_url = "https://image.pollinations.ai/prompt/"
    url = f"{base_url}{encoded_prompt}?width=1024&height=1024&model={model_choice}&nologo=true&seed={seed}"

    img2img_status = "désactivé"
    if use_img2img:
        ref_url = get_original_image_url()
        if "TON_PSEUDO_GITHUB" not in ref_url:
            encoded_ref = urllib.parse.quote(ref_url, safe="")
            url += f"&image={encoded_ref}&strength={strength}"
            img2img_status = f"activé (strength={strength})"
        else:
            img2img_status = "désactivé (Pseudo GitHub non configuré)"

    # ─── 3. Appel API ───
    progress(0.3, desc="Génération en cours... (30-60 sec)")

    try:
        response = requests.get(url, timeout=180)
        progress(0.85, desc="Traitement de l'image...")

        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            progress(1.0, desc="Terminé ! ✅")
            status_msg = (
                f"✅ Poster généré avec succès !\n"
                f"   • Seed: {seed}\n"
                f"   • Modèle: {model_choice}\n"
                f"   • img2img: {img2img_status}"
            )
            return img, status_msg
        else:
            return None, f"❌ Erreur HTTP {response.status_code}"
    except Exception as e:
        return None, f"❌ Erreur: {str(e)}"


# ─── 4. Interface Gradio ───
with gr.Blocks(title="Vocab Poster Generator", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🎨 English Vocabulary Poster Generator\nModifie ton poster avec Pollinations AI")

    with gr.Row():
        with gr.Column(scale=1):
            clothing_input = gr.Textbox(label="👗 Style de vêtements (fille)", value="Spring outfit")
            title_input = gr.Textbox(label="🏷️ Titre central", value="At the School")
            
            with gr.Row():
                obj1_input = gr.Textbox(label="Objet 1", value="Water bottle")
                obj2_input = gr.Textbox(label="Objet 2", value="Jump rope")
            with gr.Row():
                obj3_input = gr.Textbox(label="Objet 3", value="Stopwatch")
                obj4_input = gr.Textbox(label="Objet 4", value="Windbreaker")

            with gr.Accordion("⚙️ Paramètres avancés", open=False):
                model_choice = gr.Dropdown(choices=["flux", "turbo"], value="flux", label="🤖 Modèle IA")
                seed_input = gr.Number(label="🎲 Seed (-1 = aléatoire)", value=-1, precision=0)
                use_img2img = gr.Checkbox(label="🔗 Utiliser img2img (référence l'image originale)", value=True)
                strength_slider = gr.Slider(minimum=0.1, maximum=1.0, value=0.7, step=0.1, label="💪 Force de modification")

            generate_btn = gr.Button("🎨 Générer le poster", variant="primary", size="lg")

        with gr.Column(scale=1):
            gr.Markdown("### ✨ Poster généré")
            output_image = gr.Image(label="Résultat", interactive=False, height=500)
            status_output = gr.Textbox(label="📊 Statut", interactive=False, lines=4)

    generate_btn.click(
        fn=modify_image,
        inputs=[clothing_input, title_input, obj1_input, obj2_input, obj3_input, obj4_input, 
                model_choice, seed_input, use_img2img, strength_slider],
        outputs=[output_image, status_output]
    )

if __name__ == "__main__":
    app.launch()
