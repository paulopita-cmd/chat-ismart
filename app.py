from flask import Flask, render_template, request, jsonify
from openai import AzureOpenAI
import os

app = Flask(__name__)

# Configurações do Azure
client = AzureOpenAI(
    api_key=os.environ["AZURE_API_KEY"],
    api_version="2024-10-01-preview",
    azure_endpoint=os.environ["ENDPOINT"]
)

AGENT_ID = os.environ["AZURE_AGENT_ID"]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json["message"]
    try:
        response = client.agents.chat_completions.create(
            agent_id=AGENT_ID,
            messages=[{"role": "user", "content": user_message}]
        )
        reply = response.output_text
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": f"Erro: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
