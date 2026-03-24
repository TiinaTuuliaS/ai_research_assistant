import gradio as gr
from datetime import datetime
import os

from .crew import AiResearchAssistant
from .pdf_utils import create_pdf


def run_research(topic, language):
    inputs = {
        "topic": topic,
        "current_year": str(datetime.now().year),
        "language": language
    }

    try:
        result = AiResearchAssistant().crew().kickoff(inputs=inputs)

        # 🔥 tallenna txt
        os.makedirs("reports", exist_ok=True)
        safe_topic = topic.replace(" ", "_")

        txt_path = f"reports/{safe_topic}.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(str(result))

        # 🔥 tallenna pdf
        pdf_path = f"reports/{safe_topic}.pdf"
        create_pdf(str(result), pdf_path)

        return str(result), txt_path, pdf_path

    except Exception as e:
        return f"Virhe: {e}", None, None


# UI
with gr.Blocks(title="AI Research Assistant") as app:

    gr.Markdown("# 🔎 AI Research Assistant")

    with gr.Row():
        topic_input = gr.Textbox(label="Tutkimusaihe", placeholder="esim. asustetrendit 2026")

        language = gr.Dropdown(
            choices=["suomi", "english"],
            value="suomi",
            label="Kieli"
        )

    run_button = gr.Button("🚀 Suorita tutkimus")

    output = gr.Textbox(label="Raportti", lines=20)

    txt_file = gr.File(label="Lataa TXT")
    pdf_file = gr.File(label="Lataa PDF")

    run_button.click(
        fn=run_research,
        inputs=[topic_input, language],
        outputs=[output, txt_file, pdf_file]
    )


if __name__ == "__main__":
    app.launch()