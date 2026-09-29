---
name: botoes-carregando
description: Padrão do AnotAI para botões que enviam algo (submit de formulário, exclusão, sair, filtrar). Use ao criar ou alterar qualquer formulário, botão de envio ou ação POST nos templates, para o botão mostrar spinner, bloquear duplo envio e voltar ao normal ao navegar, voltar ou falhar.
---

# Botões com estado de "carregando"

Todo botão que envia algo mostra spinner + texto ("Salvando...") e fica inerte até a
resposta chegar. Isso já vem pronto: **não escreva script novo por formulário.**

## Como o projeto faz

- Um único script, [static/js/carregando.js](../../../static/js/carregando.js), carregado no `base.html`.
  Ele escuta o evento `submit` de **qualquer** `<form>` da página.
- No envio, o botão que enviou (`event.submitter`) troca o conteúdo por um spinner do
  Bootstrap e o texto, ganha a classe `btn-carregando` (CSS em `financeiro.css`,
  `pointer-events: none`) e `aria-busy`/`aria-disabled`.
- O formulário recebe `data-enviando="1"`: um segundo envio (duplo clique, Enter
  repetido) é cancelado.

## Por que `aria-disabled` e não `disabled`

Botão `disabled` no meio do envio pode ficar de fora dos dados do POST (se tiver
`name`/`value`) e não recebe foco. O botão inerte por CSS mantém tudo funcionando.

## Quando o botão volta ao estado original (o ponto mais importante)

| Situação | O que restaura |
| --- | --- |
| Usuário navega e usa o "voltar" (cache de navegação, bfcache) | `pagehide` (a foto guardada já fica limpa) e `pageshow` (garantia extra) |
| A resposta não troca de página (download, rede caiu, envio abortado) | tempo limite de 20 s (`TEMPO_LIMITE_MS`) |
| Validação no navegador ou outro script cancelou o envio | nem entra em carregando: o listener fica na fase de bolha e confere `defaultPrevented` |
| Servidor devolve o formulário com erros | página nova, HTML no estado original |
| Recarregar a página | HTML no estado original |

Regra: **nunca deixe o botão preso.** Se criar outro fluxo de envio, ele precisa
passar por `AnotAI.carregando.restaurar()` em algum destes caminhos.

## O que fazer ao criar telas

1. **Formulário comum:** use o partial `financeiro/_form-acoes.html` (Cancelar + ação
   principal). Ele já traz `data-texto-carregando`. Não crie botões submit soltos.
2. **Botão fora do partial** (filtro, sair, ação em menu): basta ser `type="submit"`
   dentro de um `<form>`. Personalize o texto com `data-texto-carregando="Filtrando..."`.
   Sem o atributo, o texto é "Enviando...".
3. **Envio por JavaScript** (`form.submit()` não dispara o evento `submit`, como na
   exclusão do Bootbox em `confirmacoes.js`): chame antes
   `AnotAI.carregando.iniciar(elemento, 'Excluindo...')`.
4. **Exceção:** formulário que não navega e não deve travar botão (raro) leva
   `data-sem-carregando`. Justifique no template com um comentário.
5. **Não** use `btnLoading`, nem `btn.disabled = true` manual, nem outro spinner:
   isso foi substituído por este padrão.

## Textos padrão

| Ação | Texto |
| --- | --- |
| Salvar, criar, atualizar | `Salvando...` |
| Excluir | `Excluindo...` |
| Entrar | `Entrando...` |
| Sair | `Saindo...` |
| Filtrar | `Filtrando...` |
| Outros | `Enviando...` (padrão) |

## Como testar

- Automatizado: o script não tem teste unitário. Cubra ao menos que os templates de
  formulário incluam `_form-acoes.html` (ver `financeiro/tests.py`).
- No navegador, para cada formulário novo:
  1. clique em enviar e confirme spinner e texto, sem mudar a largura do botão;
  2. clique duas vezes rápido: só um envio;
  3. envie, espere carregar a próxima página e volte com o botão do navegador: o
     botão precisa estar normal e clicável;
  4. envie com erro de validação do servidor: o formulário volta com o botão normal.
