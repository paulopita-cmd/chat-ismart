import os
import json
from flask import Flask, request, render_template, jsonify
from openai import AzureOpenAI
import azure.cognitiveservices.speech as speechsdk

app = Flask(__name__)

# Config OpenAI (Agents API)
client = AzureOpenAI(
    api_key=os.getenv("AZURE_API_KEY"),
    api_version="2024-10-01-preview",
    azure_endpoint=os.getenv("ENDPOINT")
)

assistant_id = os.getenv("AZURE_AGENT_ID")

# Config Speech SDK
speech_key = os.getenv("SPEECH_KEY")
speech_region = os.getenv("SPEECH_REGION")

def speech_to_text(audio_file):
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    audio_config = speechsdk.audio.AudioConfig(filename=audio_file)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    result = recognizer.recognize_once()
    return result.text if result.reason == speechsdk.ResultReason.RecognizedSpeech else ""

def text_to_speech(text, filename="static/output.wav"):
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    audio_config = speechsdk.audio.AudioOutputConfig(filename=filename)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    synthesizer.speak_text_async(text).get()
    return filename

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    response = client.agents.chat_completions.create(
        agent_id=assistant_id,
        messages=[{"role": "user", "content": user_input}]
    )
    reply = response.output_text

    # salva conversa
    with open("conversas.jsonl", "a") as f:
        f.write(json.dumps({"user": user_input, "assistant": reply}) + "\n")

    return jsonify({"reply": reply})

@app.route("/stt", methods=["POST"])
def stt():
    if "file" not in request.files:
        return jsonify({"error": "no file"}), 400
    file = request.files["file"]
    filename = "temp_audio.wav"
    file.save(filename)
    text = speech_to_text(filename)
    return jsonify({"text": text})

@app.route("/tts", methods=["POST"])
def tts():
    text = request.json.get("text")
    filename = text_to_speech(text)
    return jsonify({"audio_url": "/" + filename})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
