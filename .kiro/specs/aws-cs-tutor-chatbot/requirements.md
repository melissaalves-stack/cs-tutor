# Documento de Requisitos

## Introdução

O AWS CS Tutor Chatbot é uma aplicação web de chat que ajuda o usuário a aprender ferramentas e serviços da AWS por meio de analogias e referências ao jogo Counter-Strike. O objetivo é tornar o aprendizado de conceitos de nuvem mais divertido e memorável, associando serviços da AWS a elementos familiares do jogo (como armas, mapas, economia de rodada, funções de time e mecânicas de partida).

A aplicação é construída em Python com Flask, expõe uma página de chat e uma rota de API que envia a mensagem do usuário para o Amazon Bedrock e devolve a resposta gerada pelo modelo. A personalidade do bot (tutor de AWS com referências de Counter-Strike) é definida em uma constante `SYSTEM_PROMPT` no `app.py`.

## Glossário

- **Aplicacao**: A aplicação web Flask completa, composta pelo servidor `app.py` e pela página `templates/index.html`.
- **Servidor_Web**: O componente Flask em `app.py` responsável por servir a página de chat e processar as requisições HTTP.
- **Pagina_Chat**: A interface de chat renderizada a partir de `templates/index.html`, exibida na rota `/`.
- **Endpoint_Chat**: A rota `/chat` (método POST) que recebe a mensagem do usuário e devolve a resposta do bot.
- **Bot_Tutor**: A persona de tutor de AWS com referências de Counter-Strike, definida pela constante `SYSTEM_PROMPT` em `app.py`.
- **Cliente_Bedrock**: O cliente boto3 do serviço `bedrock-runtime` usado para invocar o modelo via `invoke_model`.
- **Modelo**: O modelo de linguagem identificado por `us.anthropic.claude-haiku-4-5-20251001-v1:0` (perfil de inferência).
- **SYSTEM_PROMPT**: A constante em `app.py` que define a personalidade, o tom e os limites do Bot_Tutor.
- **Mensagem_Usuario**: O texto enviado pelo usuário no corpo JSON da requisição ao Endpoint_Chat, no campo `message`.
- **Resposta_Bot**: O texto gerado pelo Modelo e devolvido ao usuário no campo `reply`.
- **Credenciais_AWS**: As credenciais de acesso à AWS fornecidas exclusivamente por variáveis de ambiente.

## Requisitos

### Requisito 1: Exibição da página de chat

**User Story:** Como usuário, quero acessar uma página de chat no navegador, para que eu possa conversar com o tutor de AWS.

#### Critérios de Aceitação

1. WHEN uma requisição HTTP GET é recebida na rota `/`, THE Servidor_Web SHALL retornar a Pagina_Chat renderizada a partir de `templates/index.html` com status 200.
2. THE Pagina_Chat SHALL apresentar um campo de entrada de texto para a Mensagem_Usuario e um controle de envio acionável por clique.
3. WHEN o usuário envia uma Mensagem_Usuario pela Pagina_Chat, THE Pagina_Chat SHALL exibir a Mensagem_Usuario na área de conversa em até 1 segundo.
4. WHEN a Resposta_Bot correspondente é recebida, THE Pagina_Chat SHALL exibi-la na área de conversa em ordem cronológica abaixo da Mensagem_Usuario.
5. IF o usuário aciona o controle de envio com o campo de entrada vazio ou contendo apenas espaços em branco, THEN THE Pagina_Chat SHALL impedir o envio da requisição.

### Requisito 2: Processamento de mensagens no endpoint de chat

**User Story:** Como usuário, quero enviar uma mensagem e receber uma resposta, para que eu possa tirar dúvidas sobre ferramentas da AWS.

#### Critérios de Aceitação

1. WHEN uma requisição HTTP POST é recebida na rota `/chat` com um corpo JSON válido contendo o campo `message` como uma string não vazia (após remoção de espaços em branco nas extremidades) com no máximo 4000 caracteres, THE Endpoint_Chat SHALL encaminhar a Mensagem_Usuario ao Cliente_Bedrock e retornar um corpo JSON contendo o campo `reply` com a Resposta_Bot e status 200.
2. IF a requisição POST em `/chat` contém o campo `message` ausente, nulo, ou que resulte em string vazia após remoção de espaços em branco nas extremidades, THEN THE Endpoint_Chat SHALL retornar status 400 com um corpo JSON contendo um campo de erro indicando que a mensagem é obrigatória, sem encaminhar a requisição ao Cliente_Bedrock.
3. IF a requisição POST em `/chat` contém o campo `message` com mais de 4000 caracteres, THEN THE Endpoint_Chat SHALL retornar status 400 com um corpo JSON contendo um campo de erro indicando que a mensagem excede o tamanho máximo permitido, sem encaminhar a requisição ao Cliente_Bedrock.
4. IF a requisição POST em `/chat` possui corpo ausente ou que não seja um JSON válido, THEN THE Endpoint_Chat SHALL retornar status 400 com um corpo JSON contendo um campo de erro indicando que o corpo da requisição é inválido, sem encaminhar a requisição ao Cliente_Bedrock.
5. THE Servidor_Web SHALL configurar `app.json.ensure_ascii = False` para que a Resposta_Bot seja serializada com acentos legíveis.

### Requisito 3: Geração de respostas via Amazon Bedrock

**User Story:** Como usuário, quero que as respostas venham de um modelo de linguagem da AWS, para que o conteúdo seja relevante e contextualizado.

#### Critérios de Aceitação

1. THE Cliente_Bedrock SHALL ser criado via boto3 para o serviço `bedrock-runtime` na região `us-east-1`.
2. WHEN o Endpoint_Chat processa uma Mensagem_Usuario válida, THE Cliente_Bedrock SHALL invocar o Modelo por meio de `invoke_model` usando exatamente o identificador `us.anthropic.claude-haiku-4-5-20251001-v1:0`.
3. WHEN o Cliente_Bedrock invoca o Modelo, THE Servidor_Web SHALL incluir o conteúdo integral da constante SYSTEM_PROMPT na requisição ao Modelo.
4. WHEN o Modelo retorna uma resposta de sucesso, THE Endpoint_Chat SHALL extrair o texto gerado pelo Modelo e devolvê-lo como Resposta_Bot ao usuário.
5. IF a invocação do Modelo falhar ou lançar exceção, THEN THE Endpoint_Chat SHALL devolver uma resposta de erro ao usuário indicando que a resposta não pôde ser gerada, sem expor detalhes internos da exceção.
6. IF as credenciais AWS não estiverem disponíveis nas variáveis de ambiente no momento da invocação, THEN THE Endpoint_Chat SHALL devolver uma resposta de erro ao usuário indicando falha de configuração de acesso ao serviço.

### Requisito 4: Persona do tutor de AWS com referências de Counter-Strike

**User Story:** Como usuário, quero que o bot explique serviços da AWS usando analogias de Counter-Strike, para que eu aprenda de forma mais divertida e memorável.

#### Critérios de Aceitação

1. THE SYSTEM_PROMPT SHALL definir o Bot_Tutor como um tutor de ferramentas e serviços da AWS.
2. THE SYSTEM_PROMPT SHALL instruir o Bot_Tutor a explicar conceitos da AWS utilizando analogias e referências ao jogo Counter-Strike.
3. WHEN a Mensagem_Usuario pede explicação sobre uma ferramenta ou serviço da AWS, THE Bot_Tutor SHALL produzir uma Resposta_Bot que contém pelo menos uma referência explícita a um elemento, mecânica ou termo de Counter-Strike.
4. IF a Mensagem_Usuario trata de assunto não relacionado a AWS ou a aprendizado de nuvem, THEN THE Bot_Tutor SHALL redirecionar a conversa de volta ao tema de ferramentas da AWS sem responder ao conteúdo fora do escopo.
5. WHEN o Bot_Tutor produz uma Resposta_Bot, THE Resposta_Bot SHALL estar em português do Brasil.
6. THE SYSTEM_PROMPT SHALL instruir o Bot_Tutor a responder em português do Brasil e a redirecionar assuntos fora do escopo de volta ao tema de AWS.

### Requisito 5: Gestão de credenciais da AWS

**User Story:** Como desenvolvedor, quero que as credenciais da AWS fiquem fora do código, para que eu mantenha a aplicação segura.

#### Critérios de Aceitação

1. WHEN a Aplicacao é iniciada, THE Aplicacao SHALL obter as Credenciais_AWS exclusivamente a partir de variáveis de ambiente, sem recorrer a valores embutidos no código ou a arquivos de configuração versionados.
2. THE Aplicacao SHALL manter o código-fonte livre de valores literais de Credenciais_AWS, incluindo access key ID, secret access key e session token.
3. IF uma ou mais variáveis de ambiente de Credenciais_AWS exigidas estiverem ausentes ou vazias no momento da inicialização, THEN THE Aplicacao SHALL interromper a inicialização e apresentar uma mensagem de erro indicando quais credenciais estão faltando, sem expor os valores das credenciais.
4. IF uma invocação ao serviço externo falhar por Credenciais_AWS inválidas ou expiradas, THEN THE Aplicacao SHALL retornar uma resposta de erro indicando falha de autenticação, sem expor os valores das credenciais.

### Requisito 6: Tratamento de falhas na invocação do modelo

**User Story:** Como usuário, quero receber uma indicação clara quando algo der errado, para que eu saiba que a resposta não foi gerada.

#### Critérios de Aceitação

1. IF a invocação do Modelo pelo Cliente_Bedrock falha, THEN THE Endpoint_Chat SHALL retornar status HTTP 500 com um corpo JSON contendo um campo de mensagem de erro em texto legível indicando que a resposta não pôde ser gerada.
2. IF a invocação do Modelo pelo Cliente_Bedrock excede 30 segundos sem resposta, THEN THE Endpoint_Chat SHALL interromper a espera e retornar status HTTP 500 com um corpo JSON contendo um campo de mensagem de erro em texto legível indicando falha na comunicação com o Modelo.
3. WHEN a invocação do Modelo falha, THE Servidor_Web SHALL manter o processo em execução e permanecer disponível para atender requisições subsequentes sem necessidade de reinício.
4. IF a invocação do Modelo pelo Cliente_Bedrock falha, THEN THE Endpoint_Chat SHALL retornar o corpo JSON com acentos legíveis (sem escape de caracteres não-ASCII).

### Requisito 7: Configuração de execução e dependências

**User Story:** Como desenvolvedor, quero executar a aplicação localmente com dependências declaradas, para que eu possa rodar e testar o chatbot.

#### Critérios de Aceitação

1. THE Aplicacao SHALL declarar as dependências `flask` e `boto3` em um arquivo `requirements.txt` localizado na raiz do projeto, cada uma em uma linha separada.
2. WHEN a Aplicacao é iniciada com o comando `python app.py`, THE Servidor_Web SHALL escutar requisições HTTP em `localhost` (host `127.0.0.1`) na porta `5000`.
3. IF a porta `5000` já estiver em uso no momento da inicialização, THEN THE Servidor_Web SHALL encerrar o processo de inicialização e exibir no terminal uma mensagem de erro indicando que a porta está indisponível.
4. IF alguma das dependências declaradas em `requirements.txt` não estiver instalada no ambiente quando a Aplicacao for iniciada, THEN THE Aplicacao SHALL encerrar a inicialização e exibir no terminal uma mensagem de erro indicando qual dependência está ausente.
