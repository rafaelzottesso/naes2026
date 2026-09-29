---
name: bootbox
description: Use sempre que for escrever um alert(), confirm() ou prompt() nativo do JavaScript, um diálogo modal, uma confirmação (inclusive exclusão) ou uma tela de carregamento no front-end deste projeto Django. Troca pelo Bootbox com título, conteúdo e botão em português; a única exceção é o diálogo de espera, que mostra o spinner e não tem botão.
---

## Regra

Nunca gere `alert(...)`, `confirm(...)` ou `prompt(...)`. Use o Bootbox.

Todo diálogo tem as três partes, sempre explícitas:

1. `title` — título curto do que está acontecendo.
2. `message` — o conteúdo. Cita o registro quando a ação mexe em um dado (nunca "Tem certeza?").
3. `buttons` — pelo menos um botão, com `label` em português e `className` do projeto.

A única exceção é o diálogo de carregamento: tem `title` e `message` com o spinner, e **não** tem `buttons`.

## Botões

Use só estas classes (as cores já estão no CSS do Fluxo):

| Papel | Classe | Rótulo típico |
| --- | --- | --- |
| Ação principal | `btn-primary` | `OK`, `Salvar`, `Sim` |
| Cancelar | `btn-outline-secondary` | `Cancelar` |
| Excluir | `btn-danger` | `Sim, excluir` |

Não invente classe nova e não use `btn-secondary` nem `btn-success`.

## Qual função usar

- Aviso, um botão → `bootbox.alert`
- Sim ou não → `bootbox.confirm`
- Texto digitado pelo usuário → `bootbox.prompt`
- Dois ou mais botões com ações próprias → `bootbox.dialog`
- Operação que trava a tela (upload, chamada longa, relatório) → `bootbox.dialog` de carregamento

O `base.html` já carrega jQuery, o bundle do Bootstrap 5 e `bootbox.min.js` 6.0.0, nessa ordem, e inclui `static/js/confirmacoes.js`. Não duplique esses scripts.

## Aviso

```javascript
bootbox.alert({
  title: 'Parcela quitada',
  message: 'A parcela 2 foi marcada como paga.',
  buttons: {
    ok: { label: 'OK', className: 'btn-primary' }
  }
});
```

## Confirmação

```javascript
bootbox.confirm({
  title: 'Quitar parcela',
  message: 'Quitar a parcela 2 de Aluguel?',
  buttons: {
    confirm: { label: 'Sim', className: 'btn-primary' },
    cancel: { label: 'Cancelar', className: 'btn-outline-secondary' }
  },
  callback: function (confirmado) {
    if (!confirmado) return;
    // só aqui segue a ação
  }
});
```

## Entrada de texto

`bootbox.prompt` também leva `title`, `message` e `buttons`. `null` no callback é cancelamento.

```javascript
bootbox.prompt({
  title: 'Observação',
  message: 'Escreva uma observação para esta parcela.',
  buttons: {
    confirm: { label: 'Salvar', className: 'btn-primary' },
    cancel: { label: 'Cancelar', className: 'btn-outline-secondary' }
  },
  callback: function (valor) {
    if (valor === null) return;
  }
});
```

## Vários botões

```javascript
bootbox.dialog({
  title: 'Lançamento',
  message: 'O que fazer com este lançamento?',
  buttons: {
    cancelar: { label: 'Cancelar', className: 'btn-outline-secondary' },
    salvar: {
      label: 'Salvar',
      className: 'btn-primary',
      callback: function () {}
    }
  }
});
```

## Carregamento

Sem `buttons` e com `closeButton: false`. O conteúdo é o spinner do Bootstrap 5 mais um texto. Feche com `.modal('hide')` quando a operação terminar — não coloque botão "Fechar".

```javascript
var caixa = bootbox.dialog({
  title: 'Salvando',
  message: '<p class="mb-0"><span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Aguarde...</p>',
  closeButton: false
});
// quando terminar:
caixa.modal('hide');
```

O submit comum de formulário **não** abre esse diálogo. O `<form class="btnLoading">` já troca o botão de envio pelo spinner e pelo texto "Salvando...". Mantenha essa classe; não substitua por um Bootbox.

## Exclusão

Não escreva outro `bootbox.confirm` de exclusão. O clique em `a.js-excluir` já abre o diálogo em `static/js/confirmacoes.js` (confirmar `btn-danger` "Sim, excluir", cancelar `btn-outline-secondary` "Cancelar") e só então envia o POST com o CSRF.

No link da `DeleteView`:

```html
<a class="js-excluir" href="{% url 'categoria-delete' categoria.pk %}"
   data-titulo="Excluir categoria"
   data-mensagem="Excluir a categoria {{ categoria.nome }}?">Excluir</a>
```

- `data-titulo`: `Excluir <o que é>`.
- `data-mensagem`: nome do registro. Se apagar o pai apaga os filhos, diga isso (como no lançamento, que avisa que as parcelas também saem).
- Nunca tire essa confirmação para encurtar o fluxo.
