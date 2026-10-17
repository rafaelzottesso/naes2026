# Plano: app `ia` (porta de entrada para modelos de IA)

Etapa de leitura. Nenhum código foi alterado.

## 1. Visão do projeto

**Apps**
- `naes2026`: configuração (`settings.py`, `urls.py`, `wsgi.py`, `asgi.py`).
- `website`: página inicial (`IndexView`), com contagens e últimos lançamentos do usuário.
- `financeiro`: cadastros (Categoria, Centro, Pessoa, FormaPagamento), Lancamento e Parcela, dashboard, filtros (django-filter), `services.py` (`gerar_parcelas`), comando `popular_financeiro` e templatetags (`fin_tags`, `pagination_tags`).
- Apps de terceiros em uso: `crispy_forms`, `crispy_bootstrap5`, `django_filters`, `debug_toolbar`.
- O app `ia` ainda não existe.

**Versão do Django:** 5.2.14 (`requirements.txt`). O comentário de `settings.py` cita 5.2.11, e `comandos.txt` cita 5.2.12. Ambos estão desatualizados.

**Model de usuário:** padrão do Django, `django.contrib.auth.models.User` (`AUTH_USER_MODEL` não definido).

**TIME_ZONE:** `America/Sao_Paulo`. `USE_TZ = True` e `LANGUAGE_CODE = 'pt-br'`.

**Carregamento do `.env`:** não é carregado. Não existe arquivo `.env`, não há `python-dotenv` no `requirements.txt` e `settings.py` não lê variáveis de ambiente. `os.environ` aparece só em `manage.py`, `asgi.py` e `wsgi.py`, para definir `DJANGO_SETTINGS_MODULE`. `app.yaml` tem `env_variables` com um placeholder.

**Template base:** `financeiro/templates/financeiro/base.html`, usado também por `website`.
- Blocos: `title`, `breadcrumb`, `content` e `extra_js`.
- Navbar fixa no topo, mensagens do Django e rodapé.
- Framework de CSS: Bootstrap 5.3.3 via CDN, com `bootstrap-icons` 1.11.3, DataTables 2.1.8, Bootbox 6.0.0 e jQuery 3.7.1. CSS próprio em `static/css/financeiro.css`.

**Chave primária:** `BigAutoField` (`DEFAULT_AUTO_FIELD`), inteiro de 64 bits. Não é UUID.

**Entidade dona dos dados:** hoje não existe conta, empresa ou loja.
- O dono é o usuário, pela FK `criado_por` (para `auth.User`, `PROTECT`) presente em todos os modelos.
- As consultas filtram por `criado_por=request.user`.
- O plano de conta (`docs/plano-conta-membro.md`) prevê os modelos Conta, Membro e Convite, com as decisões já tomadas. Ele não está implementado: a última migração é `0008_criado_por_protect`, e as 0009 a 0011 não existem.
- Quando o plano entrar, o usuário se liga à conta por Membro, e os dados passam a ter FK `conta`.

## 2. O que já existe de IA

Nenhuma.

- Buscas no projeto (sem `venv`, `node_modules` e migrações) por `google.genai`, `from google import genai`, `google.generativeai`, `openai`, `anthropic`, `GEMINI` e `API_KEY` não retornaram nenhum resultado no código do projeto.
- `google-genai` não está no `requirements.txt`. Também não estão `pydantic`, `Pillow` nem `pypdf`.
- Não existe model de configuração de IA.

## 3. Propostas

**Dono da cota**
- Hoje: o usuário (`criado_por`).
- Com o plano de conta: a Conta. A cota é um gasto da casa, e não de uma pessoa só. Até lá, a cota fica no usuário.

**Chamadas**

Não há chamadas existentes para propor. Para as futuras:

| Chamada | Finalidade | Referência | Motivo |
| --- | --- | --- | --- |
| Chatbot (futuro) | `chatbot_responder` | `referencia_app='chatbot'` e `referencia_id` = id da conversa | Agrupa o uso por conversa. Sem conversa salva, a referência fica nula. |
| Extração de dados de nota (hipótese, pelas libs Pillow e pypdf pedidas) | `financeiro_extrair_nota` | `referencia_app='financeiro'` e `referencia_id` = id do lançamento | Mostra o custo por lançamento. Como o lançamento ainda não existe na chamada, a referência fica nula até ser salvo. Depende da pergunta 3. |

**Referência neutra:** dois campos sem FK, `referencia_app` (texto) e `referencia_id` (inteiro, opcional). Assim o app `ia` não depende de `financeiro` nem do chatbot.

## 4. Riscos

- **Chave no código:** `SECRET_KEY` e a URL do banco, com usuário e senha, estão escritas em `naes2026/settings.py`. Como o arquivo é versionado, qualquer pessoa com acesso ao repositório lê a credencial. Recomendo mover para variáveis de ambiente e trocar as credenciais.
- **Chave da IA:** não há mecanismo seguro para carregar `GEMINI_API_KEY`. O `.env` não é lido, e o `.gitignore` não ignora `.env`. O `app.yaml` também é versionado e tem `env_variables`, então a chave não pode ir para lá.
- **Dados pessoais:** Pessoa tem nome, CPF ou CNPJ, CEP, endereço e cidade. Lançamento tem descrição e número de nota. Enviar isso à IA transfere esses dados ao Google, sem minimização.
- **Sem limite:** não há cota, limite nem controle de custo para chamadas de IA.
- **Configurações de produção:** `DEBUG = True` e `ALLOWED_HOSTS = ['*']` em `settings.py`.
- **Dependência fora da lista:** carregar `.env` sem `python-dotenv` exige código próprio ou uma biblioteca fora das permitidas.
- **Registro de chamadas:** guardar prompt e resposta vaza dados pessoais para o banco.

## 5. Perguntas

1. **Dono da cota:** a cota fica no usuário agora e passa para a Conta depois, ou espera a Conta existir antes de começar? Sugestão: começar no usuário (`criado_por`) e migrar para a Conta quando o plano de conta entrar.
2. **Limite e bloqueio:** a cota é um total de tokens por dono, por mês civil no fuso `America/Sao_Paulo`, e a chamada que passaria do limite é bloqueada antes de ir ao provedor? Sugestão: sim, limite mensal por dono, com bloqueio antes da chamada e mensagem ao usuário.
3. **Referência neutra:** a referência é o par `referencia_app` e `referencia_id`, sem FK, e a extração de nota é uma funcionalidade prevista? Sugestão: sim para o par sem FK; a extração de nota só entra se você confirmar que ela existe.
4. **Dados pessoais enviados à IA:** CPF ou CNPJ, CEP e endereço da Pessoa podem ser enviados? Sugestão: não; enviar só o necessário (descrição, valor, categoria e data).
5. **Carregar `.env`:** aceita incluir `python-dotenv` no `requirements.txt`, apesar de ela estar fora da lista permitida, ou prefere um leitor simples de `.env` escrito no projeto? Sugestão: `python-dotenv`, por ser pequena e padrão de mercado.
6. **Registro de chamadas:** guardar prompt e resposta, ou só metadados? Sugestão: só metadados (usuário, finalidade, tokens, duração, situação e referência), sem texto de prompt nem de resposta.

## 6. Decisões

- **Provedor:** Vertex AI (enterprise), e não a API key do Gemini. O app roda no App Engine e usa a mesma conta de faturamento.
- **Autenticação:** pela conta de serviço do App Engine (credenciais padrão do Google Cloud). Não há `GEMINI_API_KEY`. Isso substitui o item "Chave da IA" da seção 4.
- **Cliente:** `google-genai` com `vertexai=True`, `project` e `location`, lidos de configuração. Os valores de projeto e região não são segredo.
- **Vale para o restante do plano:** qualquer menção à API key nas próximas etapas deve ser lida como Vertex AI.
- **Pendente:** as perguntas 1 a 4 e 6 seguem sem resposta. A pergunta 5 (`python-dotenv`) perde a urgência, pois não há mais segredo a carregar do `.env`.
