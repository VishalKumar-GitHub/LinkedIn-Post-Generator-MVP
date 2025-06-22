import requests
import gradio as gr
import requests


# Your GROQ API key (hidden from users)
API_KEY = "GORQ_API_KEY"

# Function to call GROQ API
def generate_text(prompt, model="llama3-8b-8192", temperature=0.7):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        result = response.json()
        return result['choices'][0]['message']['content']
    else:
        return f"Error: {response.status_code} - {response.text}"

# UI
with gr.Blocks(css="body {background-color: #007BFF; color: white;}") as demo:
    gr.Markdown(
        "<h1 style='text-align: center; font-size: 48px; margin-top: 40px;'>Linkedin Post Generator</h1>"
    )

    prompt = gr.Textbox(
        label="Enter your idea for a LinkedIn Post",
        placeholder="Type your topic here...",
        lines=3
    )
    generate_btn = gr.Button("Generate", elem_id="generate-btn")
    output = gr.Textbox(label="Generated Post", lines=8)

    generate_btn.click(
        fn=generate_text,
        inputs=[prompt],
        outputs=output
    )

# Additional styling for button (optional)
demo.launch()
