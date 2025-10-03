from flask import Flask, request, jsonify, render_template
import os, json
from datetime import datetime
import openai
import azure.cognitiveservices.speech as speechsdk

app = Flask(__name__)

# Configuração Azure OpenAI
openai.api_key = os.getenv("AZURE_API_KEY")
openai.api_base = os.getenv("ENDPOINT")
openai.api_type = "azure"
openai.api_version = "2024-05-01-preview"
agent_id = os.getenv("AZURE_AGENT_ID")

# Configuração Azure Speech
speech_key = os.getenv("SPEECH_KEY")
speech_region = os.getenv("SPEECH_REGION")

# Arquivo de log
LOG_FILE = "conversas.jsonl"

def salvar_conversa(usuario, resposta):
    registro = {
        "timestamp": datetime.utcnow().isoformat(),
        "usuario": usuario,
        "resposta": resposta
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message")

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": user_message}]
    )

    reply = response["choices"][0]["message"]["content"]
    salvar_conversa(user_message, reply)
    return jsonify({"reply": reply})

@app.route("/stt", methods=["POST"])
def stt():
    audio_file = request.files["audio"]
    file_path = "temp_audio.wav"
    audio_file.save(file_path)

    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    audio_config = speechsdk.audio.AudioConfig(filename=file_path)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    result = recognizer.recognize_once()

    return jsonify({"text": result.text})

@app.route("/tts", methods=["POST"])
def tts():
    data = request.json
    text = data.get("text")

    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    file_name = f"static/output_{datetime.utcnow().timestamp()}.wav"
    audio_config = speechsdk.audio.AudioOutputConfig(filename=file_name)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    synthesizer.speak_text_async(text).get()

    return jsonify({"audio_file": file_name})

if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    app.run(host="0.0.0.0", port=5000)
