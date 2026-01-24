from __future__ import annotations

import os
import requests
import gradio as gr


API_URL = os.getenv("API_URL", "http://localhost:8000")


def generate(mode: str, seed: int):
    response = requests.post(
        f"{API_URL}/cards", json={"mode": mode, "seed": seed}, timeout=10
    )
    return response.json()


with gr.Blocks() as demo:
    gr.Markdown("# Scenario Card Generator")
    mode = gr.Dropdown(["casual", "narrative", "matched"], value="casual")
    seed = gr.Number(value=1, precision=0)
    out = gr.JSON()
    btn = gr.Button("Generate")
    btn.click(generate, inputs=[mode, seed], outputs=out)


if __name__ == "__main__":
    demo.launch(
        server_name=os.getenv("UI_HOST", "0.0.0.0"),
        server_port=int(os.getenv("UI_PORT", "7860")),
    )
