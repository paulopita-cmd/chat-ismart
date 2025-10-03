import os
from flask import Flask, request, jsonify, render_template
from openai import AzureOpenAI
import azure.cognitiveservices.speech as speechsdk

app = Flask(__name__)

# Configuração do Azure OpenAI
client = AzureOpenAI(
    api_key=os.getenv("AZURE_API_KEY"),
    api_version="2024-05-01-preview",
    azure_endpoint=os.getenv("ENDPOINT")
)

AZURE_AGENT_ID = os.getenv("AZURE_AGENT_ID")

# Configuração do Azure Speech
SPEECH_KEY = os.getenv("SPEECH_KEY")
SPEECH_REGION = os.getenv("SPEECH_REGION")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "")

        if not user_message:
            return jsonify({"error": "Mensagem vazia"}), 400

        response = client.agents.create_response(
            agent_id=AZURE_AGENT_ID,
            input=[{"role": "user", "content": user_message}]
        )

        reply_blocks = []
        for output in response.output:
            if output["type"] == "message":
                for c in output["content"]:
                    if c["type"] == "output_text":
                        reply_blocks.append(c["text"])

        return jsonify({"reply": reply_blocks})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/tts", methods=["POST"])
def tts():
    try:
        data = request.get_json()
        text = data.get("text", "")

        if not text:
            return jsonify({"error": "Texto vazio"}), 400

        speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
        audio_config = speechsdk.audio.AudioOutputConfig(filename="static/output.wav")

        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        synthesizer.speak_text_async(text).get()

        return jsonify({"audio_url": "/static/output.wav"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
