import os
from flask import Flask, request, jsonify, render_template
from openai import AzureOpenAI
import azure.cognitiveservices.speech as speechsdk

app = Flask(__name__)

# Azure OpenAI client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_API_KEY"),
    api_version="2024-10-01-preview",
    azure_endpoint=os.getenv("ENDPOINT")
)

# Rota principal (HTML)
@app.route("/")
def index():
    return render_template("index.html")

# Rota de chat com streaming
@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")

    stream = client.chat.completions.create(
        model=os.getenv("AZURE_DEPLOYMENT"),
        messages=[
            {"role": "system", "content": "Você é um agente que ajuda jovens do Ismart a ensaiar suas apresentações de Projeto de Vida."},
            {"role": "user", "content": user_message}
        ],
        stream=True
    )

    final_text = ""
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        final_text += delta

    return jsonify({"reply": final_text})

# Rota para Text-to-Speech
@app.route("/tts", methods=["POST"])
def tts():
    text = request.json.get("text", "")

    speech_config = speechsdk.SpeechConfig(
        subscription=os.getenv("SPEECH_KEY"),
        region=os.getenv("SPEECH_REGION")
    )
    speech_config.speech_synthesis_voice_name = "pt-BR-FranciscaNeural"

    file_name = "static/response.wav"
    audio_config = speechsdk.audio.AudioOutputConfig(filename=file_name)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    synthesizer.speak_text_async(text).get()

    return jsonify({"audio_url": f"/{file_name}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
