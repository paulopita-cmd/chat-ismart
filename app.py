from flask import Flask, render_template, request
import requests
import os

app = Flask(__name__)

# Configuração: chave e endpoint do Azure
API_KEY = os.getenv("AZURE_API_KEY")
ENDPOINT = "https://SEU-ENDPOINT.openai.azure.com/openai/deployments/Agente_Bancas_Ismart/chat/completions?api-version=2024-08-01-preview"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.form["message"]
    headers = {"Content-Type": "application/json", "api-key": API_KEY}
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
    return reply

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
