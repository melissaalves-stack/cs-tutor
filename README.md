<div align="center">

# CS Tutor

### Chatbot com IA que ensina AWS usando analogias de Counter-Strike

Aprender computação em nuvem pode ser tão intuitivo quanto um round de CS. O CS Tutor traduz conceitos da AWS (EC2, S3, Lambda, IAM e mais) em linguagem gamer, usando analogias com armas, economia de rodada, callouts e mapas de Counter-Strike.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Web-000000?logo=flask&logoColor=white)
![AWS](https://img.shields.io/badge/Amazon%20Bedrock-Claude%20Haiku%204.5-FF9900?logo=amazonaws&logoColor=white)

</div>

---

## Sobre o projeto

CS Tutor é uma aplicação web de chat que conversa com o usuário e explica ferramentas e serviços da AWS de um jeito descontraído, sempre usando referências ao universo de Counter-Strike. A resposta é gerada em tempo real por um modelo de linguagem da Amazon, com personalidade, tom e limites definidos por um prompt de sistema.

O foco do projeto é demonstrar, de ponta a ponta, uma integração limpa entre um frontend leve e um modelo de IA generativa hospedado na nuvem, com atenção a tratamento de erros, validação de entrada e segurança de credenciais.

### Destaques técnicos

- Integração direta com o **Amazon Bedrock** via `boto3` (`invoke_model`), usando o modelo **Claude Haiku 4.5**.
- Backend **Flask** enxuto: uma rota serve a interface e outra processa o chat, retornando JSON.
- **Validação de entrada** antes de qualquer chamada ao modelo (corpo inválido, mensagem vazia e tamanho máximo).
- **Tratamento de erros** que traduz falhas de infraestrutura em respostas claras, sem vazar detalhes internos.
- **Segurança de credenciais**: as chaves AWS são lidas exclusivamente de variáveis de ambiente, nunca ficam no código.
- Interface responsiva com identidade visual inspirada na estética tática de Counter-Strike 2.

---

## Tecnologias

| Camada | Stack |
| --- | --- |
| Linguagem | Python 3.12 |
| Web framework | Flask |
| SDK AWS | boto3 |
| IA generativa | Amazon Bedrock — Claude Haiku 4.5 |
| Frontend | HTML, CSS e SVG (sem dependências externas de JS) |

---

## Como executar

Pré-requisitos: Python 3 instalado e uma conta AWS com acesso ao Amazon Bedrock habilitado na região `us-east-1`.

**1. Clone o repositório**

```bash
git clone <url-do-repositorio>
cd cs-tutor
```

**2. Instale as dependências**

```bash
pip install -r requirements.txt
```

**3. Configure as variáveis de ambiente AWS** (requer credenciais próprias)

```bash
export AWS_ACCESS_KEY_ID="sua-access-key"
export AWS_SECRET_ACCESS_KEY="sua-secret-key"
```

**4. Execute a aplicação**

```bash
python3 app.py
```

**5. Acesse no navegador**

```
http://127.0.0.1:5000
```

---

## Nota

Este projeto requer uma conta AWS com acesso ao **Amazon Bedrock** e ao modelo Claude Haiku 4.5 liberado na região `us-east-1`. As credenciais são de responsabilidade do usuário e devem ser fornecidas via variáveis de ambiente.

---

## Contexto

Projeto criado no **II Workshop de Ciência da Computação da UNIFAL-MG** (Universidade Federal de Alfenas), em outubro de 2026.
