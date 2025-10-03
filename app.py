import os
from flask import Flask, render_template, request, jsonify
from openai import AzureOpenAI

app = Flask(__name__)

# Configuração Azure
AZURE_API_KEY = os.getenv("AZURE_API_KEY")
AZURE_ENDPOINT = os.getenv("ENDPOINT")
AZURE_DEPLOYMENT = os.getenv("AZURE_DEPLOYMENT", "gpt-4o")

client = AzureOpenAI(
    api_key=AZURE_API_KEY,
    api_version="2024-05-01-preview",
    azure_endpoint=AZURE_ENDPOINT
)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")

    try:
        response = client.chat.completions.create(
            model=AZURE_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "Você é um avaliador de banca do Ismart, dê devolutivas claras e construtivas."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500,
            temperature=0.7
        )
        reply = response.choices[0].message.content
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": f"Erro: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
