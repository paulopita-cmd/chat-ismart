from flask import Flask, render_template, request, jsonify
import openai
import os
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, AudioConfig

app = Flask(__name__)

# Configurações do Azure
AZURE_API_KEY = os.getenv("AZURE_API_KEY")
AZURE_ENDPOINT = os.getenv("ENDPOINT")
AZURE_DEPLOYMENT = os.getenv("AZURE_DEPLOYMENT")
AZURE_AGENT_ID = os.getenv("AZURE_AGENT_ID")
SPEECH_KEY = os.getenv("SPEECH_KEY")
SPEECH_REGION = os.getenv("SPEECH_REGION")

openai.api_key = AZURE_API_KEY
openai.api_base = AZURE_ENDPOINT
openai.api_type = "azure"
openai.api_version = "2024-05-01-preview"

# Perfis de banca
profiles = {
    "academico": "Você é uma banca rigorosa, avaliando clareza, lógica e conteúdo acadêmico com atenção crítica.",
    "acolhedora": "Você é uma banca acolhedora, dando incentivo e feedback em tom encorajador e motivacional.",
    "desafiadora": "Você é uma banca desafiadora, pressionando o aluno a aprofundar ideias e sendo crítico em pontos fracos."
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    profile = request.json.get("profile", "acolhedora")

    system_prompt = profiles.get(profile, profiles["acolhedora"])

    try:
        response = openai.ChatCompletion.create(
            engine=AZURE_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )

        reply = response["choices"][0]["message"]["content"]

        # Geração de áudio com Azure Speech
        speech_config = SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
        audio_config = AudioConfig(filename="static/response.wav")
        synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        synthesizer.speak_text_async(reply)

        return jsonify({"reply": reply, "audio_url": "/static/response.wav"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
