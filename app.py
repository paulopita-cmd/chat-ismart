from flask import Flask, render_template, request, jsonify
from openai import AzureOpenAI
import os

app = Flask(__name__)

# Config OpenAI
client = AzureOpenAI(
    api_key=os.getenv("AZURE_API_KEY"),
    api_version="2024-05-01-preview",
    base_url=f"{os.getenv('ENDPOINT')}/openai/deployments/{os.getenv('AZURE_DEPLOYMENT')}"
)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_DEPLOYMENT"),
            messages=[
                {"role": "system", "content": "Você é uma banca avaliadora do Ismart, sempre respeitosa e construtiva."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=300,
            temperature=0.7
        )
        bot_reply = response.choices[0].message.content
        return jsonify({"reply": bot_reply})
    except Exception as e:
        return jsonify({"reply": f"Erro: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
