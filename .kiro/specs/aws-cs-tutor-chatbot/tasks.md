# Plano de Implementação: AWS CS Tutor Chatbot

## Visão Geral

A implementação segue uma abordagem incremental em Python/Flask: primeiro a estrutura e as dependências, depois as constantes e configuração da aplicação (incluindo a checagem de credenciais e o cliente Bedrock), em seguida a camada de integração com o Bedrock (wrapper e extração de texto), depois a rota `/chat` com validação e tratamento de erros, a rota `/` com o frontend, e por fim o bloco de execução. Cada etapa constrói sobre a anterior e termina integrando as peças, sem código órfão. Os testes baseados em propriedades (Hypothesis + pytest) e os testes de exemplo/unitários/smoke são adicionados como subtarefas próximas ao código que validam.

A linguagem de implementação é **Python** (com Flask), conforme definido no design. Os testes de propriedade usam **Hypothesis** e **pytest** com o cliente de teste do Flask.

## Tasks

- [x] 1. Configurar estrutura do projeto e dependências
  - Criar o arquivo `requirements.txt` na raiz do projeto com `flask` e `boto3`, cada dependência em uma linha separada
  - Criar o diretório `templates/` (ainda vazio) para a página de chat
  - Criar a estrutura inicial do `app.py` na raiz com os imports necessários (`json`, `os`, `boto3`, `flask`, `botocore.config.Config` e as exceções de `botocore.exceptions`)
  - _Requisitos: 7.1_

- [x] 2. Definir constantes, exceções de domínio e persona
  - [x] 2.1 Definir constantes de módulo e exceções de domínio no `app.py`
    - Declarar `REGION = "us-east-1"`, `MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"`, `MAX_MESSAGE_LEN = 4000`, `MAX_TOKENS = 1024`, `TIMEOUT_SECONDS = 30` e `REQUIRED_AWS_ENV_VARS = ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY")`
    - Definir as classes de exceção `BedrockError(Exception)` e `CredentialsError(BedrockError)`
    - _Requisitos: 3.1, 3.2_

  - [x] 2.2 Definir a constante `SYSTEM_PROMPT` com a persona do Bot_Tutor
    - Escrever o texto da persona: tutor de ferramentas/serviços da AWS, que explica conceitos usando analogias e referências de Counter-Strike, responde em português do Brasil e redireciona assuntos fora de escopo de volta ao tema de AWS
    - _Requisitos: 4.1, 4.2, 4.6_

  - [ ]* 2.3 Escrever testes de exemplo para o conteúdo do `SYSTEM_PROMPT`
    - Verificar que o texto menciona tutor de AWS, analogias de Counter-Strike, instrução de responder em pt-BR e de redirecionar assuntos fora de escopo
    - _Requisitos: 4.1, 4.2, 4.6_

- [x] 3. Implementar a checagem de credenciais na inicialização
  - [x] 3.1 Implementar a função de verificação das variáveis de ambiente de credenciais
    - Verificar `REQUIRED_AWS_ENV_VARS`; se alguma estiver ausente ou vazia, sinalizar erro listando exatamente as variáveis faltantes (nem a mais, nem a menos), sem expor valores de credenciais
    - Obter credenciais exclusivamente de variáveis de ambiente, sem valores embutidos no código
    - _Requisitos: 5.1, 5.2, 5.3_

  - [ ]* 3.2 Escrever teste de propriedade para a checagem de credenciais ausentes
    - **Propriedade 10: A checagem de credenciais ausentes nomeia exatamente as faltantes**
    - **Validates: Requisitos 5.3**
    - Gerar subconjuntos de `REQUIRED_AWS_ENV_VARS` ausentes/vazios e verificar que a mensagem nomeia exatamente as faltantes, sem valores

  - [ ]* 3.3 Escrever teste estático para ausência de literais de credenciais no código
    - Verificar via leitura/grep do `app.py` que não há literais de access key ID, secret access key ou session token embutidos no código
    - _Requisitos: 5.1, 5.2_

- [x] 4. Configurar a aplicação Flask e o cliente Bedrock
  - [x] 4.1 Instanciar a aplicação Flask e o cliente Bedrock no escopo de módulo
    - Criar `app = Flask(__name__)` e definir `app.json.ensure_ascii = False`
    - Criar `botocore.config.Config` com `region_name=REGION`, `read_timeout=TIMEOUT_SECONDS`, `connect_timeout=TIMEOUT_SECONDS` e `retries={"max_attempts": 0}`
    - Instanciar `bedrock_client = boto3.client("bedrock-runtime", config=bedrock_config)` uma única vez no módulo
    - _Requisitos: 2.5, 3.1, 6.2, 6.4_

  - [ ]* 4.2 Escrever testes de smoke para região e timeout do cliente Bedrock
    - Verificar que a config do cliente usa `us-east-1`, `read_timeout == 30` e `connect_timeout == 30`
    - _Requisitos: 3.1, 6.2_

- [x] 5. Implementar a camada de integração com o Bedrock
  - [x] 5.1 Implementar a função `extrair_texto`
    - Concatenar, na ordem original, os campos `text` dos blocos de `content` cujo `type == "text"`, ignorando blocos de outros tipos
    - Se o texto resultante for vazio após `strip`, levantar `BedrockError`
    - _Requisitos: 3.4_

  - [ ]* 5.2 Escrever teste de propriedade para a extração de texto
    - **Propriedade 7: A extração concatena os blocos de texto da resposta**
    - **Validates: Requisitos 3.4**
    - Gerar payloads com blocos `text`/não-`text` em ordem aleatória e verificar a concatenação correta

  - [x] 5.3 Implementar a função `gerar_resposta` (wrapper do Bedrock)
    - Montar o corpo no formato Anthropic Messages API: `anthropic_version="bedrock-2023-05-31"`, `max_tokens=MAX_TOKENS`, `system=SYSTEM_PROMPT` (conteúdo integral) e `messages` com a mensagem do usuário
    - Invocar `bedrock_client.invoke_model(modelId=MODEL_ID, body=body)` usando exatamente o `MODEL_ID`
    - Traduzir exceções de infraestrutura em erros de domínio: `NoCredentialsError`/`PartialCredentialsError` e `ClientError` com códigos de autenticação (`UnrecognizedClientException`, `AccessDeniedException`, `ExpiredTokenException`, `InvalidSignatureException`) → `CredentialsError`; demais `ClientError`, `ReadTimeoutError`, `ConnectTimeoutError`, `EndpointConnectionError` → `BedrockError`
    - Ler e parsear o `body` da resposta e devolver o texto via `extrair_texto`
    - _Requisitos: 3.2, 3.3, 3.4, 3.5, 3.6, 6.1, 6.2, 5.4_

  - [ ]* 5.4 Escrever teste de propriedade para presença integral do SYSTEM_PROMPT
    - **Propriedade 6: O SYSTEM_PROMPT integral está sempre presente na invocação**
    - **Validates: Requisitos 3.3**
    - Com mensagens válidas e `invoke_model` mockado para capturar o body, verificar que `body["system"]` contém o conteúdo integral e inalterado do SYSTEM_PROMPT

  - [ ]* 5.5 Escrever teste de exemplo para o contrato de invocação do modelo
    - Mockar `invoke_model` e verificar `modelId == "us.anthropic.claude-haiku-4-5-20251001-v1:0"`
    - _Requisitos: 3.2_

- [x] 6. Checkpoint - Garantir que os testes passem
  - Garanta que todos os testes passam; pergunte ao usuário caso surjam dúvidas.

- [x] 7. Implementar a rota `/chat` (POST) com validação e tratamento de erros
  - [x] 7.1 Implementar a validação de entrada da rota `/chat`
    - Fazer parse do corpo com `request.get_json(silent=True)`; se `None` ou não for `dict` → 400 `{"error": "Corpo da requisição inválido..."}`
    - Obter `message`; se ausente, nulo, não-string ou vazio após `strip()` → 400 `{"error": "A mensagem é obrigatória."}`
    - Se `len(message) > MAX_MESSAGE_LEN` → 400 `{"error": "A mensagem excede o tamanho máximo..."}`
    - Garantir que nenhuma chamada ao Bedrock ocorre em casos de 400
    - _Requisitos: 2.2, 2.3, 2.4, 1.5_

  - [x] 7.2 Implementar o fluxo de sucesso e o tratamento de erros de serviço da rota `/chat`
    - Para entrada válida, chamar `gerar_resposta(message.strip())` e retornar 200 `{"reply": ...}`
    - Capturar `CredentialsError` → 500 `{"error": "Falha de configuração de acesso ao serviço."}`
    - Capturar `BedrockError` → 500 `{"error": "Não foi possível gerar a resposta..."}`
    - Garantir que mensagens de erro são genéricas e não expõem detalhes internos da exceção, e que a resposta usa `jsonify` (respeitando `ensure_ascii = False`)
    - _Requisitos: 2.1, 3.5, 3.6, 6.1, 6.3, 6.4_

  - [ ]* 7.3 Escrever teste de propriedade para rejeição de mensagem vazia/whitespace/ausente
    - **Propriedade 1: Mensagem vazia, só espaços ou ausente é rejeitada**
    - **Validates: Requisitos 2.2, 1.5**
    - Gerar strings de whitespace, `None` e campo ausente; verificar 400 com campo `error` e que o Bedrock não é chamado

  - [ ]* 7.4 Escrever teste de propriedade para rejeição de mensagem acima do limite
    - **Propriedade 2: Mensagem acima do limite de tamanho é rejeitada**
    - **Validates: Requisitos 2.3**
    - Gerar strings com `len > 4000` e testar a fronteira 4000/4001; verificar 400 com campo `error`

  - [ ]* 7.5 Escrever teste de propriedade para rejeição de corpo não-JSON/estrutura inválida
    - **Propriedade 3: Corpo não-JSON ou com estrutura inválida é rejeitado**
    - **Validates: Requisitos 2.4**
    - Gerar corpos que não sejam objeto JSON válido; verificar 400 com campo `error`

  - [ ]* 7.6 Escrever teste de propriedade para entrada inválida nunca invocar o Bedrock
    - **Propriedade 4: Entrada inválida nunca invoca o Bedrock**
    - **Validates: Requisitos 2.2, 2.3, 2.4**
    - Unir os geradores de P1–P3 e verificar com mock que `invoke_model` não é chamado

  - [ ]* 7.7 Escrever teste de propriedade para mensagem válida produzir 200 com `reply`
    - **Propriedade 5: Mensagem válida produz resposta de sucesso com `reply`**
    - **Validates: Requisitos 2.1**
    - Gerar strings válidas (1..4000 após strip) com Bedrock mockado para sucesso; verificar 200 com campo `reply`

  - [ ]* 7.8 Escrever teste de propriedade para preservação de acentos na serialização
    - **Propriedade 8: A serialização JSON preserva acentos**
    - **Validates: Requisitos 2.5, 6.4**
    - Gerar textos com caracteres acentuados em `reply` e `error`; verificar que o corpo JSON não contém sequências `\uXXXX`

  - [ ]* 7.9 Escrever teste de propriedade para falha de invocação resultar em 500 genérico
    - **Propriedade 9: Qualquer falha de invocação resulta em 500 sem vazar detalhes internos**
    - **Validates: Requisitos 3.5, 6.1**
    - Gerar vários tipos de exceção (genérica, timeout, conexão) no mock; verificar 500 com mensagem genérica sem detalhes internos

  - [ ]* 7.10 Escrever teste de propriedade para resiliência do processo após falha
    - **Propriedade 11: Após uma falha, a requisição seguinte continua sendo atendida**
    - **Validates: Requisitos 6.3**
    - Mockar sequência [falha, sucesso] com entrada válida; verificar que a segunda requisição retorna 200 com `reply`

  - [ ]* 7.11 Escrever testes de exemplo para edge-cases de credenciais e timeout na rota
    - Mock levanta `NoCredentialsError`/`ExpiredTokenException` → 500 com mensagem de configuração/autenticação, sem valores
    - Mock levanta `ReadTimeoutError` → 500 com mensagem de falha de comunicação
    - _Requisitos: 3.6, 5.4, 6.2_

- [x] 8. Implementar a rota `/` (GET) e o frontend
  - [x] 8.1 Implementar a rota `/` que renderiza a página de chat
    - Adicionar `@app.route("/", methods=["GET"])` retornando `render_template("index.html")` com status 200
    - _Requisitos: 1.1_

  - [x] 8.2 Criar `templates/index.html` com a interface de chat
    - Campo de entrada de texto e botão de envio acionável por clique
    - Área de conversa que exibe a mensagem do usuário imediatamente e a resposta do bot em ordem cronológica abaixo dela
    - Guarda no cliente que impede o envio quando o campo está vazio ou só com espaços em branco
    - Chamada `fetch` em `POST /chat` com `Content-Type: application/json`, exibindo `reply` em caso de sucesso e `error` em caso de falha (400/500)
    - _Requisitos: 1.2, 1.3, 1.4, 1.5_

  - [ ]* 8.3 Escrever teste de exemplo para a rota `/`
    - GET `/` retorna 200 e o HTML contém o campo de entrada e o botão de envio
    - _Requisitos: 1.1, 1.2_

- [x] 9. Integrar e finalizar a execução da aplicação
  - [x] 9.1 Implementar o bloco de execução `__main__`
    - Invocar a checagem de credenciais da inicialização antes de subir o servidor
    - Executar `app.run(host="127.0.0.1", port=5000)` no bloco `if __name__ == "__main__":`
    - Garantir que o processo encerra com mensagem clara em caso de porta 5000 indisponível (`OSError`) e que dependências ausentes falham no import nomeando o módulo
    - _Requisitos: 7.2, 7.3, 7.4_

  - [ ]* 9.2 Escrever teste de exemplo para o conteúdo de `requirements.txt`
    - Ler o arquivo e verificar que contém `flask` e `boto3`, um por linha
    - _Requisitos: 7.1_

  - [ ]* 9.3 Escrever teste de smoke para host e porta de execução
    - Verificar (via mock de `app.run`) que `host="127.0.0.1"` e `port=5000` são usados na inicialização
    - _Requisitos: 7.2_

- [x] 10. Checkpoint final - Garantir que todos os testes passem
  - Garanta que todos os testes passam; pergunte ao usuário caso surjam dúvidas.

## Notas

- Tarefas marcadas com `*` são opcionais (testes) e podem ser puladas para um MVP mais rápido, mas são recomendadas para garantir a correção.
- Cada tarefa referencia requisitos específicos para rastreabilidade.
- Os checkpoints garantem validação incremental.
- Os testes de propriedade (Hypothesis + pytest) validam as 11 propriedades de correção universais do backend; cada propriedade é implementada por um único teste com no mínimo 100 iterações (`@settings(max_examples=100)`) e com a tag `# Feature: aws-cs-tutor-chatbot, Property {número}: {texto}`.
- Os testes de exemplo/unitários/smoke cobrem contratos fixos, conteúdo estático, configuração e edge-cases.
- Comportamentos do LLM (analogias de CS, redirecionamento de fora de escopo, idioma pt-BR) e da UI são verificados por testes de integração/manuais, fora do escopo das tarefas de código automatizadas.
- Restrições da stack respeitadas: sem FastAPI, Django, banco de dados, LangChain, RAG ou autenticação. Credenciais AWS apenas por variáveis de ambiente.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1", "2.2", "3.1", "5.1", "8.2"] },
    { "id": 1, "tasks": ["2.3", "3.2", "3.3", "4.1", "5.2"] },
    { "id": 2, "tasks": ["4.2", "5.3", "8.1", "9.2"] },
    { "id": 3, "tasks": ["5.4", "5.5", "7.1", "8.3"] },
    { "id": 4, "tasks": ["7.2", "9.1"] },
    { "id": 5, "tasks": ["7.3", "7.4", "7.5", "7.6", "7.7", "7.8", "7.9", "7.10", "7.11", "9.3"] }
  ]
}
```
