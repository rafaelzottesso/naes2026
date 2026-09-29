# Plano: conta, membros, convites e criação de usuário

Objetivo: várias pessoas da mesma casa enxergam e lançam nos mesmos dados, sem
mudar o foco do app, que é o controle financeiro.

## Decisões já tomadas

- Os dados passam a pertencer a uma **Conta**. `criado_por`, `criado_em` e `atualizado_em` continuam em todas as classes (quem lançou e quando).
- A **conta ativa fica na sessão**, como no SIGEP. O usuário não escolhe a conta em cada formulário nem em cada filtro.
- Papéis: `dono`, `editor` e `leitor`. Não há permissão por receita ou despesa.
- Usuário novo ganha uma conta pessoal. Quem usa sozinho não percebe a mudança.
- Entrada de novos membros por **convite com aceite**, sem autocomplete.
- **O cadastro de usuário só acontece por convite** (ou pelo admin). Não existe cadastro público aberto.

## Convite

Hoje só o admin cria usuários e o projeto não tem e-mail configurado. Por isso o
convite é um **link pessoal, de uso único e com validade**, que o dono copia e
manda pelo meio que preferir (WhatsApp, por exemplo). Quem recebe:

- já tem login: entra, vê a conta e aceita ou recusa;
- ainda não tem login: cria o usuário na própria página do convite e já entra na conta.

### Fluxo do dono

1. Na tela da conta, clica em "Convidar" e informa o **e-mail** e o **papel** (`editor` ou `leitor`; `dono` só o admin atribui, ou o dono depois, pela tela de membros).
2. O sistema cria o `Convite` com um token aleatório e validade de 7 dias.
3. A tela da conta mostra o link do convite pendente, com o botão "Copiar link".
4. O dono pode **cancelar** o convite enquanto ele estiver pendente e pode gerar outro depois de cancelado ou expirado.

Regras:

- Só um convite pendente por conta e e-mail (sem diferenciar maiúsculas de minúsculas).
- Convidar quem já é membro (por e-mail) é recusado com uma mensagem genérica, para não revelar quem está cadastrado.
- O token tem 256 bits (`secrets.token_urlsafe(32)`), vale para um uso só e expira em `CONVITE_VALIDADE_DIAS` (7).
- O link serve como credencial: quem o tem entra na conta com o papel do convite. Por isso ele é de uso único, some depois de aceito, recusado, cancelado ou expirado, e o dono decide com quem compartilhar.

### Fluxo do convidado

Ao abrir `convite/<token>/`:

| Situação | O que aparece |
| --- | --- |
| Token inválido, usado, cancelado ou expirado | Página "Convite inválido ou expirado" (mesma mensagem para todos os casos). |
| Logado | Nome da conta, quem convidou, papel e os botões **Aceitar** e **Recusar** (POST). |
| Não logado e o e-mail já pertence a um usuário | Só a opção "Entrar" (com `next` de volta ao convite), para não duplicar usuário. |
| Não logado e o e-mail é novo | "Entrar" ou **"Criar minha conta"**. |

Criar minha conta (`convite/<token>/cadastro/`):

- Campos: nome de usuário, nome, e-mail (vem do convite, somente leitura), senha e confirmação (com os validadores de senha do Django).
- Numa única transação: cria o `User` (sem acesso ao admin), cria a conta pessoal, cria o `Membro` com o papel do convite, marca o convite como aceito, faz o login e define a conta convidada como conta ativa.
- Se outro convite ou usuário usar o mesmo e-mail ou nome de usuário no meio do caminho, a transação falha e o formulário mostra o erro (o convite usa `select_for_update` para não ser aceito duas vezes).

### Convites recebidos dentro do app

Usuário que já existe e ainda não abriu o link vê um aviso no topo e a lista `convite-list` com os convites pendentes cujo e-mail é o dele. A lista abre a mesma tela de aceitar ou recusar.

### Criação de usuário

- **Por convite:** fluxo acima, o único cadastro aberto ao público.
- **Pelo admin:** continua como hoje. O usuário criado ganha a conta pessoal automaticamente.
- **Conta pessoal:** criada por um sinal `post_save` do `User` (só na criação), com o usuário como dono.
- **E-mail:** o Django não exige e-mail único. A criação por convite exige que ele seja novo (sem diferenciar maiúsculas de minúsculas). Para quem já tem usuário sem e-mail, o convite só funciona pelo link, com o usuário logado.
- **Senha esquecida / e-mail:** fora do escopo. Sem servidor de e-mail, a troca continua pelo `alterar-senha` (logado) ou pelo admin.

## Modelos

Todos com `criado_por`, `criado_em` e `atualizado_em`.

**Conta**
- `nome`, `status` (Ativo).

**Membro**
- `conta` (FK, `CASCADE`), `usuario` (FK), `papel` (`dono`, `editor`, `leitor`).
- `UniqueConstraint(conta, usuario)`.
- `criado_por` é quem adicionou o membro.

**Convite**
- `conta` (FK), `email`, `papel`, `token` (único).
- `convidado` (FK para User, vazio até o aceite).
- `situacao`: `pendente`, `aceito`, `recusado`, `cancelado`, `expirado`.
- `expira_em`, `respondido_em`.
- `UniqueConstraint(conta, email)` condicionada a `situacao='pendente'` (com o e-mail sempre gravado em minúsculas).
- A propriedade `valido` é verdadeira quando está pendente e `expira_em` ainda não passou. Convites vencidos viram `expirado` ao serem consultados, sem tarefa agendada.

**Nos modelos existentes**
- `conta` (FK, `PROTECT`) em Categoria, Centro, Pessoa, FormaPagamento e Lancamento.
- Parcela usa `lancamento.conta`, sem campo próprio.
- A restrição de documento único da pessoa passa de `(criado_por, documento)` para `(conta, documento)`.
- **`criado_por` usa `PROTECT`** (decidido e já aplicado na migração `0008_criado_por_protect`). Apagar um usuário que lançou dados é bloqueado, porque esses dados podem pertencer a outra pessoa da conta. Para desligar alguém, inative o usuário (`is_active`) ou remova-o da conta. As classes novas (Conta, Membro, Convite) também nascem com `criado_por` em `PROTECT`.

## Sessão, middleware e permissões

**Middleware `ContaAtivaMiddleware`**
- Lê `session['conta_ativa_id']` e confere se o usuário é membro. Se não for, usa a primeira conta dele (ou cria a pessoal).
- Preenche `request.conta` e `request.membro`.

**Context processor**
- Expõe `conta_ativa`, `minhas_contas`, `papel` e `convites_pendentes` (quantidade) para os templates.

**Mixins em `views.py`**
- `RegistroDaContaMixin`: no lugar de `RegistroDoUsuarioMixin`. Filtra `conta=request.conta`.
- `EscritaMixin`: `dono` e `editor` podem criar, editar e excluir. `leitor` recebe 403.
- `DonoMixin`: só o dono gerencia conta, membros e convites.
- O `form_valid` das telas de criação preenche `conta` e `criado_por`.

**Trocar `criado_por` por `conta` nestes pontos**
- `views.py`: os dois mixins de acesso, as contagens das listas, os `filter(criado_por=...)` dos detalhes, o dashboard e o aviso do `LancamentoCreate`.
- `forms.py`: `_opcoes_ativas`.
- `filters.py`: os `ModelChoiceFilter` do lançamento.
- `models.py`: `_validar_dono` do Lancamento, `Parcela.clean`, `Pessoa.clean`.
- `popular_financeiro`.
- `website/views.py` (Início): confirmar as consultas ao migrar.

**Regras de negócio**
- A conta sempre tem pelo menos um dono. O último dono não pode sair, ser removido nem ser rebaixado.
- Remover um membro não apaga o que ele lançou.
- Só o dono edita a conta, muda papéis, convida, cancela convites e remove membros. Qualquer membro pode sair.
- A troca de conta ativa só aceita contas das quais o usuário é membro.

**Serviços (`financeiro/services_conta.py`)**
- `criar_conta_pessoal(user)`.
- `criar_convite(conta, email, papel, por)`.
- `aceitar_convite(convite, user)`, com transação e bloqueio da linha.
- `cadastrar_por_convite(convite, dados)`, que cria usuário, conta pessoal e membro.
- As views só chamam esses serviços, para as regras ficarem em um lugar e serem testáveis.

## URLs (seguindo o padrão do app)

| URL | Nome | Quem |
| --- | --- | --- |
| `conta/trocar/<pk>/` (POST) | `conta-trocar` | membro |
| `listar/conta/` | `conta-list` | logado |
| `cadastrar/conta/` | `conta-create` | logado |
| `detalhar/conta/<pk>/` | `conta-detail` (membros e convites) | membro |
| `atualizar/conta/<pk>/` | `conta-update` | dono |
| `convidar/conta/<pk>/` | `convite-create` | dono |
| `cancelar/convite/<pk>/` (POST) | `convite-cancelar` | dono |
| `listar/convite/` | `convite-list` (recebidos) | logado |
| `convite/<token>/` | `convite-abrir` | **público** |
| `convite/<token>/cadastro/` | `convite-cadastro` | **público** (só com convite válido) |
| `convite/<token>/aceitar/` (POST) | `convite-aceitar` | logado |
| `convite/<token>/recusar/` (POST) | `convite-recusar` | logado |
| `atualizar/membro/<pk>/` | `membro-update` (papel) | dono |
| `excluir/membro/<pk>/` | `membro-delete` (remover ou sair) | dono ou o próprio |

As duas rotas públicas não usam o mixin de login e ficam em `financeiro/urls.py`.

## Formulários

- `ContaForm`: nome e Ativo.
- `ConviteForm`: e-mail e papel (grava o e-mail em minúsculas e recusa membro existente e convite pendente repetido).
- `CadastroPorConviteForm`: baseado em `BaseUserCreationForm`, com nome de usuário, nome, e-mail (somente leitura) e senha.
- `MembroForm`: só o papel (valida a regra do último dono).

## Templates

- `list/conta.html`: minhas contas, com papel, número de membros e botão de trocar.
- `detail/conta.html`: dados da conta, tabela de membros (papel, ações) e tabela de convites (pendentes com o link e "Copiar link", mais o histórico), com o botão "Convidar".
- `list/convite.html`: convites que recebi.
- `convite/abrir.html`: a página pública do convite (inválido, entrar, criar conta ou aceitar e recusar). Usa o `base.html`, que já cobre o visitante sem login.
- `convite/cadastro.html`: formulário de criação de usuário.
- Formulários simples (conta, convite, papel do membro) reaproveitam `form.html`.
- `_seletor_conta.html`: seletor no topo (dropdown com as contas e o link "Gerenciar"), incluído no `base.html`.
- `_auditoria.html` (já existe): mostrar nas telas novas.
- Menu: "Contas" na navegação e um selo com os convites pendentes.
- Exclusão de membro e cancelamento de convite usam a confirmação do Bootbox, como as demais.
- Botão "Copiar link" com um pequeno script (clipboard), sem dependência nova.

## Configurações novas (`settings.py`)

- `CONVITE_VALIDADE_DIAS = 7`.
- Nenhuma configuração de e-mail por enquanto. Se um dia houver, o `criar_convite` passa a enviar o link além de exibi-lo.

## Migrações (em ordem)

1. **0009**: criar `Conta`, `Membro` e `Convite`; `conta` como campo aceitando nulo nos modelos existentes.
2. **0010 (dados)**: para cada usuário que tem registros, criar a conta "Pessoal de <usuário>", o `Membro` dono, e preencher `conta` em todos os registros pelo `criado_por`. Usuários sem registros ganham a conta no primeiro acesso.
3. **0011**: `conta` passa a ser obrigatória; trocar a restrição de documento único (de `(criado_por, documento)` para `(conta, documento)`).

## Testes

**Acesso e permissões**
- Usuário fora da conta recebe 404. Leitor não cria, edita nem exclui (403). Editor faz tudo, menos gerenciar membros.
- Trocar de conta muda o que aparece; trocar para conta alheia é recusado.
- O último dono não sai nem é rebaixado.

**Convite**
- Criar convite gera token, validade e link. Não convida membro, nem duplica pendente. A mensagem é igual para e-mail existente ou não.
- Aceitar e recusar (só por POST, só com login). Cancelar (só o dono).
- Token inválido, usado, cancelado ou expirado mostra a página de convite inválido, sempre igual.
- O mesmo convite não pode ser aceito duas vezes.

**Criação de usuário por convite**
- Cadastro válido cria `User` (sem `is_staff`), conta pessoal, `Membro` com o papel do convite, marca o convite como aceito, faz o login e ativa a conta convidada.
- E-mail que já pertence a um usuário não permite o cadastro (mostra só "Entrar").
- Senha fraca ou confirmação diferente é recusada e o convite continua pendente.
- Cadastro sem token válido dá 404.
- Usuário criado pelo admin também ganha a conta pessoal.

**Dados**
- Apagar um usuário que tem registros é bloqueado (`ProtectedError`); o `criado_por` nunca é apagado junto.
- Migração de dados: registros antigos ficam na conta pessoal do `criado_por`.
- Documento único por conta: a mesma pessoa pode existir em contas diferentes.
- `criado_por` é preenchido em todas as criações, e `atualizado_em` muda na edição.

## Ordem de entrega (um commit por etapa)

1. Modelos, migrações e conta pessoal automática (sinal), sem mudar telas.
2. Middleware, mixins e troca de `criado_por` por `conta` nas regras de acesso. Aqui os testes existentes precisam passar sem alteração de comportamento.
3. Seletor de conta no topo e a tela de contas.
4. Membros e a lista de membros da conta.
5. Convites: criar, copiar link, cancelar, aceitar e recusar (usuário que já existe).
6. Criação de usuário pelo link do convite.
7. Papéis (403 para leitor) e a regra do último dono.

## Fora do escopo (por enquanto)

Cadastro público aberto; envio de e-mail e recuperação de senha por e-mail; permissão por tipo, categoria ou lançamento; lançamento privado; "ver todas as contas" no dashboard; auditoria de alterações.
