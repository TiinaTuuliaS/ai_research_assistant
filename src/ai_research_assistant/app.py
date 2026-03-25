import gradio as gr
from datetime import datetime
import os
import re

from .crew import AiResearchAssistant
from .pdf_utils import create_pdf


def run_research(topic, language):
    topic = topic.strip()

    # 🔥 estä tyhjä input
    if not topic:
        return "⚠️ Anna tutkimusaihe", None, None

    inputs = {
        "topic": topic,
        "current_year": str(datetime.now().year),
        "language": language
    }

    try:
        result = AiResearchAssistant().crew().kickoff(inputs=inputs)

        if not result:
            return "❌ Raporttia ei saatu", None, None

        # 🔥 varmista kansio
        os.makedirs("reports", exist_ok=True)

        # 🔥 turvallinen tiedostonimi
        safe_topic = re.sub(r'[^a-zA-Z0-9_]', '', topic.replace(" ", "_")).lower()

        # =====================
        # TXT
        # =====================
        txt_path = f"reports/{safe_topic}.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(str(result))

        # =====================
        # PDF
        # =====================
        pdf_filename = f"{safe_topic}.pdf"
        pdf_path = create_pdf(str(result), pdf_filename)

        # =====================
        # RETURN UI:lle
        # =====================
        return f"✅ Valmis!\n\n{result}", txt_path, pdf_path

    except Exception as e:
        return f"❌ Virhe: {str(e)}", None, None


# =====================
# UI
# =====================
with gr.Blocks(title="AI Research Assistant") as app:

    gr.Markdown("# 🔎 AI Research Assistant")

    with gr.Row():
        topic_input = gr.Textbox(
            label="Tutkimusaihe",
            placeholder="esim. asustetrendit 2026"
        )

        language = gr.Dropdown(
            choices=["suomi", "english"],
            value="suomi",
            label="Kieli"
        )

    run_button = gr.Button("🚀 Suorita tutkimus", variant="primary")

    output = gr.Markdown(label="Raportti")
    txt_file = gr.File(label="Lataa TXT")
    pdf_file = gr.File(label="Lataa PDF")

    run_button.click(
        fn=run_research,
        inputs=[topic_input, language],
        outputs=[output, txt_file, pdf_file]
    )


# 🔥 tärkeä: queue tuo spinnerin automaattisesti
app.queue()

# =====================
# KÄYNNISTYS
# =====================
if __name__ == "__main__":
    app.launch()