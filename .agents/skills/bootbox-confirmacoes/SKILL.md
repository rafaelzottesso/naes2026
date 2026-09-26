---
name: bootbox-confirmacoes
description: Use sempre que for escrever um alert()/confirm()/prompt() nativo do JavaScript neste projeto Django, mostrar um estado de carregamento no front-end, ou implementar uma ação de exclusão (DeleteView, botão "Excluir" numa listagem, exclusão via AJAX) — substitui pelos diálogos do Bootbox, sempre com título, e com botões Sim/Não em português antes de excluir.
---

## Antes de gerar qualquer diálogo

Verifique se o projeto já tem uma convenção própria de botões (classes customizadas
em `static/css/`, um design system, ou botões que não sejam os padrões do Bootstrap
como `btn-primary`/`btn-danger`/`btn-secondary`). Se existir, use essas classes nos
`buttons.confirm.className` / `buttons.cancel.className`. Se não existir nenhuma
convenção própria, use os padrões do Bootstrap sem inventar uma nova.

## Instruções

1. Nunca gere `alert(...)`, `confirm(...)` ou `prompt(...)` nativos do JavaScript
   neste projeto — troque sempre pelo tipo correspondente do Bootbox:
   - Aviso simples → `bootbox.alert({ title, message })`
   - Pergunta sim/não → `bootbox.confirm({ title, message, buttons, callback })`
   - Entrada de texto → `bootbox.prompt({ title, placeholder, callback })`
   - Operação demorada (upload, chamada de IA, relatório) → `bootbox.dialog({ title,
     message: '<spinner-border do Bootstrap 5>', closeButton: false })`, fechado
     manualmente com `.modal('hide')` quando a operação terminar.
2. **Todo diálogo tem `title`** — nunca gere um Bootbox sem título, mesmo que a
   mensagem pareça autoexplicativa.
3. **O rodapé só existe quando há `buttons`.** Um diálogo de carregamento (`dialog`
   sem `buttons`) não deve ganhar um botão "Fechar" artificial — ele se fecha
   sozinho quando a operação termina.
4. Toda ação de exclusão (link/botão para uma `DeleteView`, formulário de exclusão,
   ou chamada AJAX que remove um registro) precisa ser interceptada por um
   `bootbox.confirm(...)` com:
   - `title: 'Excluir <nome do que está sendo excluído>'`.
   - Mensagem específica citando o registro (ex.: "Excluir o cliente {{ cliente.nome }}?"),
     nunca um texto genérico como "Tem certeza?".
   - Botão de confirmação rotulado "Sim, excluir" (ou a convenção do projeto — ver
     seção "Antes de gerar qualquer diálogo").
   - Botão de cancelamento rotulado "Cancelar" ou "Não".
   - O envio real (`form.submit()` ou `fetch`/AJAX) só acontece dentro do
     `callback`, quando `confirmado === true`.
5. Garanta que `bootbox.min.js` está incluído no `base.html`, depois de jQuery e do
   bundle do Bootstrap — nessa ordem.
6. Nunca remova a confirmação de exclusão para "simplificar" — é a proteção contra
   clique acidental.