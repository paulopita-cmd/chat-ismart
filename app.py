from flask import Flask, render_template, request, jsonify
import requests
import os
import datetime
import csv
import azure.cognitiveservices.speech as speechsdk

app = Flask(__name__)

# Variáveis de ambiente
AZURE_API_KEY = os.getenv("AZURE_API_KEY")
ENDPOINT = os.getenv("ENDPOINT")
SPEECH_KEY = os.getenv("SPEECH_KEY")
SPEECH_REGION = os.getenv("SPEECH_REGION")

# ==== Funções de Log ====
def log_conversa(aluno, perfil, pergunta, resposta):
    with open("conversas.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.datetime.now(), aluno, perfil, pergunta, resposta])

# ==== Chat texto → texto ====
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.form["message"]
    perfil = request.form.get("perfil", "não informado")
    aluno = request.form.get("aluno", "anonimo")

    headers = {"Content-Type": "application/json", "api-key": AZURE_API_KEY}
    payload = {
        "messages": [
            {"role": "system", "content": "Você é o agente do Ismart que simula bancas avaliadoras."},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7,
        "top_p": 0.9
    }
    response = requests.post(ENDPOINT, headers=headers, json=payload)
    reply = response.json()["choices"][0]["message"]["content"]

    # Salva log
    log_conversa(aluno, perfil, user_message, reply)

    return reply

# ==== Voz (Speech-to-Text) ====
@app.route("/stt", methods=["POST"])
def stt():
    audio_file = request.files["audio"]
    path = "temp.wav"
    audio_file.save(path)

    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    audio_input = speechsdk.AudioConfig(filename=path)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)
    result = recognizer.recognize_once()
    return jsonify({"text": result.text})

# ==== Voz (Text-to-Speech) ====
@app.route("/tts", methods=["POST"])
def tts():
    text = request.json.get("text", "")
    filename = "static/response.wav"

    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    audio_output = speechsdk.audio.AudioOutputConfig(filename=filename)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_output)
    synthesizer.speak_text_async(text).get()

    return jsonify({"audio": filename})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
