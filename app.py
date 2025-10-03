import os
import json
import uuid
from flask import Flask, request, jsonify, render_template, send_from_directory
import requests
from datetime import datetime
import azure.cognitiveservices.speech as speechsdk

app = Flask(__name__, static_folder="static", template_folder="templates")

# Config from environment
AZURE_API_KEY = os.environ.get("AZURE_API_KEY")
AZURE_ENDPOINT = os.environ.get("ENDPOINT")
AZURE_DEPLOYMENT = os.environ.get("AZURE_DEPLOYMENT", "gpt-4o")
SPEECH_KEY = os.environ.get("SPEECH_KEY")
SPEECH_REGION = os.environ.get("SPEECH_REGION")

CONV_FILE = "conversations.json"

def load_conversations():
    if os.path.exists(CONV_FILE):
        with open(CONV_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_conversation(entry):
    convs = load_conversations()
    convs.append(entry)
    with open(CONV_FILE, "w", encoding="utf-8") as f:
        json.dump(convs, f, ensure_ascii=False, indent=2)

def query_azure_openai(prompt):
    if not AZURE_API_KEY or not AZURE_ENDPOINT:
        raise RuntimeError("Azure API key or endpoint not configured in environment.")
    url = f"{AZURE_ENDPOINT}/openai/deployments/{AZURE_DEPLOYMENT}/chat/completions?api-version=2024-08-01-preview"
    headers = {"Content-Type": "application/json", "api-key": AZURE_API_KEY}
    data = {
        "messages": [
            {"role": "system", "content": (
                "Você é um agente que ajuda jovens do Ismart a ensaiar sua apresentação de Projeto de Vida. "
                "Dê feedback construtivo em blocos curtos e cheque compreensão com 'Entendeu até aqui?' entre blocos. "
                "Use os perfis 1:Rigor Acadêmico, 2:Acolhedora, 3:Desafiadora quando apropriado."
            )},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.7,
        "top_p": 0.9
    }
    resp = requests.post(url, headers=headers, json=data, timeout=30)
    resp.raise_for_status()
    result = resp.json()
    return result["choices"][0]["message"]["content"]

def synthesize_to_file(text, filename):
    if not SPEECH_KEY or not SPEECH_REGION:
        raise RuntimeError("Speech key or region not configured.")
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    try:
        speech_config.speech_synthesis_voice_name = "pt-BR-FranciscaNeural"
    except Exception:
        pass
    audio_output = speechsdk.audio.AudioOutputConfig(filename=filename)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_output)
    synthesizer.speak_text_async(text).get()
    return filename

def transcribe_file(path):
    if not SPEECH_KEY or not SPEECH_REGION:
        raise RuntimeError("Speech key or region not configured.")
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    audio_input = speechsdk.AudioConfig(filename=path)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)
    result = recognizer.recognize_once()
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    else:
        return ""

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/chat', methods=['POST'])
def chat():
    payload = request.json or {}
    user_message = payload.get("message", "")
    profile = payload.get("profile", "1")
    student = payload.get("student", "anonimo")
    try:
        reply = query_azure_openai(user_message)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "student": student,
        "profile": profile,
        "user": user_message,
        "agent": reply
    }
    save_conversation(entry)
    return jsonify({"reply": reply})

@app.route('/stt', methods=['POST'])
def stt():
    if 'audio' not in request.files:
        return jsonify({"error": "no audio file"}), 400
    f = request.files['audio']
    uid = str(uuid.uuid4())
    temp_path = f"static/input_{uid}.wav"
    f.save(temp_path)
    try:
        text = transcribe_file(temp_path)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"text": text})

@app.route('/speak', methods=['POST'])
def speak():
    data = request.json or {}
    text = data.get("text", "")
    if not text:
        return jsonify({"error": "no text"}), 400
    uid = str(uuid.uuid4())
    out_filename = f"static/response_{uid}.wav"
    try:
        synthesize_to_file(text, out_filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    audio_url = f"/static/{os.path.basename(out_filename)}"
    return jsonify({"audio": audio_url})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
