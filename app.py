import json
import os

import boto3
from flask import Flask, request, jsonify, render_template
from botocore.config import Config
from botocore.exceptions import (
    NoCredentialsError,
    PartialCredentialsError,
    ClientError,
    ReadTimeoutError,
    ConnectTimeoutError,
    EndpointConnectionError,
)

# ---------------------------------------------------------------------------
# Constantes de módulo (Task 2.1)
# ---------------------------------------------------------------------------

REGION = "us-east-1"
MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
MAX_MESSAGE_LEN = 4000
MAX_TOKENS = 1024
TIMEOUT_SECONDS = 30
REQUIRED_AWS_ENV_VARS = ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY")

# ---------------------------------------------------------------------------
# Exceções de domínio (Task 2.1)
# ---------------------------------------------------------------------------


class BedrockError(Exception):
    pass


class CredentialsError(BedrockError):
    pass

# ---------------------------------------------------------------------------
# SYSTEM_PROMPT (Task 2.2)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
IDENTIDADE
Você é CS tutor, uma aplicação web de chat que ajuda o usuário a aprender ferramentas e serviços da AWS por meio de analogias e referências ao jogo Counter-Strike.
Você fala com estudante de TI.
Seu tom é descontraído, animado e encorajador.

REGRAS DE FORMATO
Nunca use markdown: sem asteriscos duplos, sem cerquilha, sem traços em listas.
Responda em no máximo 3 parágrafos curtos.
Nunca faça perguntas de volta ao usuário.
Sempre termine com uma frase de ação ou conclusão.

RESTRIÇÃO TEMÁTICA
Se o usuário perguntar algo fora do tema de computação em nuvem, responda:
"Isso foge do meu escopo, mas posso te ajudar com o aprendizado de conceitos de nuvem."

EXEMPLOS (few-shot)
Veja como eu devo responder:
Usuário: amigo, me ajude a entender buckets s3
Bot: claro parceiro! um bucket s3 é como o seu inventário da Steam, onde cada arquivo guardado é um objeto (como uma skin ou caixa), identificado pelo seu caminho único chamado key, e protegido por permissões que definem se o seu inventário é privado só para você ou público para qualquer um acessar.
""".strip()

# ---------------------------------------------------------------------------
# Checagem de credenciais na inicialização (Task 3.1)
# ---------------------------------------------------------------------------


def verificar_credenciais():
    """Verifica a presença das credenciais AWS nas variáveis de ambiente.

    As credenciais são obtidas exclusivamente de variáveis de ambiente
    (sem valores embutidos no código). Uma variável é considerada faltante
    quando está ausente ou vazia (incluindo strings compostas apenas por
    espaços em branco).

    Levanta ``CredentialsError`` com uma mensagem que nomeia exatamente as
    variáveis faltantes, na mesma ordem de ``REQUIRED_AWS_ENV_VARS``, sem
    expor os valores das credenciais. Se todas estiverem presentes, retorna
    normalmente.
    """
    faltantes = [
        nome
        for nome in REQUIRED_AWS_ENV_VARS
        if os.environ.get(nome, "").strip() == ""
    ]
    if faltantes:
        raise CredentialsError(
            "Credenciais AWS ausentes ou vazias nas variáveis de ambiente: "
            + ", ".join(faltantes)
        )

# ---------------------------------------------------------------------------
# Aplicação Flask e cliente Bedrock (Task 4.1)
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.json.ensure_ascii = False

bedrock_config = Config(
    region_name=REGION,
    read_timeout=TIMEOUT_SECONDS,
    connect_timeout=TIMEOUT_SECONDS,
    retries={"max_attempts": 0},
)
bedrock_client = boto3.client("bedrock-runtime", config=bedrock_config)

# ---------------------------------------------------------------------------
# Camada de integração com o Bedrock (Tasks 5.1, 5.3)
# ---------------------------------------------------------------------------


def extrair_texto(payload: dict) -> str:
    """Extrai o texto gerado de um payload de resposta Anthropic Messages.

    O campo ``content`` é uma lista de blocos. Esta função concatena, na ordem
    original, o campo ``text`` dos blocos cujo ``type`` é ``"text"``, ignorando
    blocos de outros tipos. Se o texto resultante for vazio após ``strip``,
    levanta ``BedrockError``.
    """
    blocos = payload.get("content", [])
    partes = [b.get("text", "") for b in blocos if b.get("type") == "text"]
    texto = "".join(partes).strip()
    if texto == "":
        raise BedrockError()
    return texto


def gerar_resposta(mensagem: str) -> str:
    """Invoca o Modelo via Bedrock e devolve a Resposta_Bot como texto.

    Monta o corpo no formato Anthropic Messages API incluindo o conteúdo
    integral de ``SYSTEM_PROMPT`` no campo ``system`` e a mensagem do usuário
    em ``messages``. Invoca ``invoke_model`` usando exatamente ``MODEL_ID`` e
    traduz as exceções de infraestrutura em erros de domínio
    (``CredentialsError`` / ``BedrockError``), sem expor detalhes internos.
    Em caso de sucesso, extrai o texto gerado via ``extrair_texto``.
    """
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": MAX_TOKENS,
        "system": SYSTEM_PROMPT,
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": mensagem}]}
        ],
    })
    try:
        resp = bedrock_client.invoke_model(modelId=MODEL_ID, body=body)
    except (NoCredentialsError, PartialCredentialsError):
        raise CredentialsError()
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in (
            "UnrecognizedClientException",
            "AccessDeniedException",
            "ExpiredTokenException",
            "InvalidSignatureException",
        ):
            raise CredentialsError()
        raise BedrockError()
    except (ReadTimeoutError, ConnectTimeoutError, EndpointConnectionError):
        raise BedrockError()

    payload = json.loads(resp["body"].read())
    return extrair_texto(payload)


# ---------------------------------------------------------------------------
# Rotas (Tasks 7.x, 8.1)
# ---------------------------------------------------------------------------


@app.route("/", methods=["GET"])
def index():
    """Serve a Pagina_Chat renderizada a partir de ``templates/index.html``.

    Responde a requisições HTTP GET na rota ``/`` com o HTML da página de
    chat e status 200 (Requisito 1.1).
    """
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    """Processa a Mensagem_Usuario e devolve a Resposta_Bot (Tasks 7.1, 7.2).

    Validação de entrada antes de qualquer chamada ao Bedrock, na ordem:
    corpo inválido -> mensagem obrigatória -> tamanho máximo. Em qualquer
    caso de 400, o Cliente_Bedrock não é invocado. Para entrada válida,
    chama ``gerar_resposta`` e devolve 200 com ``reply``; traduz erros de
    domínio em respostas 500 genéricas, sem expor detalhes internos. Todas
    as respostas usam ``jsonify`` (respeitando ``ensure_ascii = False``).
    """
    # --- Validação de entrada (Task 7.1) ---
    data = request.get_json(silent=True)
    if data is None or not isinstance(data, dict):
        return jsonify({"error": "Corpo da requisição inválido. Envie um JSON válido."}), 400

    message = data.get("message")
    if not isinstance(message, str) or message.strip() == "":
        return jsonify({"error": "A mensagem é obrigatória."}), 400

    if len(message) > MAX_MESSAGE_LEN:
        return jsonify({"error": "A mensagem excede o tamanho máximo permitido (4000 caracteres)."}), 400

    # --- Fluxo de sucesso e tratamento de erros de serviço (Task 7.2) ---
    try:
        reply = gerar_resposta(message.strip())
    except CredentialsError:
        return jsonify({"error": "Falha de configuração de acesso ao serviço."}), 500
    except BedrockError:
        return jsonify({"error": "Não foi possível gerar a resposta. Tente novamente."}), 500

    return jsonify({"reply": reply}), 200


# ---------------------------------------------------------------------------
# Execução da aplicação (Task 9.1)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Verifica as credenciais AWS antes de subir o servidor (Requisito 7.3/5.3).
    # Em caso de ausência, encerra o processo com código não-zero exibindo a
    # mensagem da exceção, que nomeia exatamente as variáveis faltantes sem
    # expor seus valores.
    try:
        verificar_credenciais()
    except CredentialsError as exc:
        raise SystemExit(str(exc))

    # Sobe o servidor em localhost:5000 (Requisito 7.2). Se a porta 5000 já
    # estiver em uso, o bind falha com OSError e o processo encerra com uma
    # mensagem clara indicando a indisponibilidade da porta (Requisito 7.3).
    try:
        app.run(host="127.0.0.1", port=5000)
    except OSError as exc:
        raise SystemExit(f"Porta 5000 indisponível: {exc}")
