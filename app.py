
import os, uuid
from flask import Flask, render_template, request, jsonify, make_response
from openai import AzureOpenAI

app = Flask(__name__)

# ===== Azure OpenAI client =====
client = AzureOpenAI(
    api_key=os.getenv("AZURE_API_KEY"),
    api_version="2024-05-01-preview",
    azure_endpoint=os.getenv("ENDPOINT")
)
MODEL = os.getenv("AZURE_DEPLOYMENT", "gpt-4o")

# ===== Memória simples em RAM por sessão =====
SESSIONS = {}  # sid -> { 'profile': 'academico|acolhedora|desafiadora', 'next_block': int, 'user_text': str }

BASE_RULES = (
    "Você é um agente que ajuda jovens do Ismart a ensaiar sua apresentação de Projeto de Vida para uma banca simulada. "
    "Siga estritamente as regras:
"
    "1) Nunca entregue tudo de uma vez.
"
    "2) Sempre responda em blocos numerados (Bloco 1, Bloco 2, ...), cada um focado em um aspecto (estrutura, clareza, emoção, impacto, evidências, etc.).
"
    "3) Ao final de cada bloco, SEMPRE pergunte: 'Entendeu até aqui? Quer que eu continue ou aprofunde algum ponto?'
"
    "4) Pare após UM ÚNICO BLOCO. Aguarde a resposta do aluno para seguir.
"
    "5) Alinhe-se aos princípios do Ismart: autoconhecimento, protagonismo, resiliência, ética, transformação social e mentalidade de crescimento. "
    "Quando útil, conecte ao Projeto Pedagógico do Ismart, ao Roteiro de Projeto de Vida e ao livro 'Sonho Grande' (sem citar nomes específicos)."
)

PROFILE_TONES = {
    "academico": (
        "Perfil: Rigor Acadêmico. Tom formal, crítico e respeitoso. Valorize clareza conceitual, consistência lógica e uso de evidências. "
        "Conecte perguntas às competências de Aprendizagem e Curiosidade. Finalize cada bloco com uma sugestão prática."
    ),
    "acolhedora": (
        "Perfil: Acolhedora. Tom empático, motivador e construtivo. Valorize conquistas, fortaleça a autoestima e reconheça o esforço. "
        "Conecte perguntas a Inclusão, Pertencimento, Comunidade, Resiliência e Bem-Estar. Termine com reforço de confiança."
    ),
    "desafiadora": (
        "Perfil: Desafiadora. Tom firme e provocador, sempre respeitoso. Questione argumentos, levante hipóteses contrárias e peça justificativas sólidas. "
        "Conecte a Autonomia e Protagonismo, e mostre pontos de fragilidade para reflexão."
    ),
}

def get_sid(resp=None):
    sid = request.cookies.get("sid")
    if not sid:
        sid = uuid.uuid4().hex
        if resp is None:
            resp = make_response()
        resp.set_cookie("sid", sid, httponly=False, samesite="Lax")
    return sid, resp

@app.route("/")
def index():
    resp = make_response(render_template("index.html"))
    # garante cookie de sessão simples
    sid, resp = get_sid(resp)
    if sid not in SESSIONS:
        SESSIONS[sid] = {"profile": None, "next_block": 1, "user_text": ""}
    return resp

@app.route("/select_profile", methods=["POST"])
def select_profile():
    sid = request.cookies.get("sid")
    data = request.get_json(force=True)
    profile = data.get("profile")
    if profile not in PROFILE_TONES:
        return jsonify({"ok": False, "error": "Perfil inválido"}), 400
    if sid not in SESSIONS:
        SESSIONS[sid] = {"profile": profile, "next_block": 1, "user_text": ""}
    else:
        SESSIONS[sid]["profile"] = profile
        SESSIONS[sid]["next_block"] = 1
    return jsonify({"ok": True})

@app.route("/chat", methods=["POST"])
def chat():
    sid = request.cookies.get("sid")
    if sid not in SESSIONS:
        SESSIONS[sid] = {"profile": None, "next_block": 1, "user_text": ""}
    state = SESSIONS[sid]

    data = request.get_json(force=True)
    user_msg = (data.get("message") or "").strip()

    # Caso não tenha perfil escolhido ainda
    if not state["profile"]:
        welcome = (
            "Olá! Bem-vindo ao seu treino de Projeto de Vida no Ismart. "
            "Escolha a banca para treinar hoje: 1) Rigor Acadêmico, 2) Acolhedora, 3) Desafiadora. "
            "Digite 1, 2 ou 3 para começarmos."
        )
        return jsonify({"reply": welcome})

    # Detecta 'continuar' vs novo texto
    low = user_msg.lower()
    is_continue = low in {"sim", "pode continuar", "pode seguir", "continuar", "segue", "ok", "sim, pode continuar", "s", "vai"}

    # Se o aluno enviou um texto muito curto (e não for 'continuar'), pedimos para colar o conteúdo
    if not is_continue and len(user_msg) < 12 and not state["user_text"]:
        return jsonify({"reply": "Pode colar o trecho da sua apresentação para eu começar o Bloco 1? 😊"})

    # Se é um novo texto longo, registramos como contexto e reiniciamos para o Bloco 1
    if len(user_msg) >= 12 and not is_continue:
        state["user_text"] = user_msg
        state["next_block"] = 1

    # Monta instruções
    block_no = state["next_block"]
    profile_key = state["profile"]
    tone = PROFILE_TONES.get(profile_key, PROFILE_TONES["acolhedora"])

    system_prompt = (
        BASE_RULES + " "
        + tone + " "
        + f"RESPONDA AGORA APENAS O 'Bloco {block_no}'. Termine com a pergunta de checagem e PARE."
    )

    # Constrói a entrada do usuário para o modelo
    if state["user_text"]:
        user_payload = (
            f"Perfil selecionado: {profile_key}. "
            f"Este é o texto do aluno para análise (contexto contínuo):

{state['user_text']}

"
            f"Continue a partir do Bloco {block_no}. Responda somente UM bloco, finalize com a checagem e pare."
        )
    else:
        user_payload = (
            f"Perfil selecionado: {profile_key}. O aluno ainda não colou um texto longo. "
            f"Inicie com Bloco {block_no} focando em estrutura/clareza para ajudar a organizar a apresentação. "
            f"Responda UM bloco, finalize com a checagem e pare."
        )

    # Chamada ao modelo
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_payload},
            ],
            temperature=0.7,
            max_tokens=600,
        )
        reply = resp.choices[0].message.content
    except Exception as e:
        reply = f"Erro ao gerar resposta: {e}"

    # Prepara próximo passo: só avança o contador após enviar um bloco
    state["next_block"] = block_no + 1
    return jsonify({"reply": reply})
