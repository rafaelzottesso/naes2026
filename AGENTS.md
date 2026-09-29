# AnotAI — finanças pessoais

Projeto Django de controle financeiro pessoal. Cada usuário vê e altera só o que ele mesmo cadastrou (`criado_por`). O Django Admin continua enxergando tudo.

## Modelos e o que cada um pode fazer

| Modelo | Criar | Listar | Ver | Editar | Excluir |
| --- | --- | --- | --- | --- | --- |
| Categoria | sim | sim | sim | sim | sim, se nenhum lançamento usar |
| Centro de lançamento | sim | sim | sim | sim | sim, se nenhum lançamento usar |
| Pessoa | sim | sim | sim | sim | sim, se nenhum lançamento usar |
| Forma de pagamento | sim | sim | sim | sim | sim, se nenhum lançamento ou parcela usar |
| Lançamento | sim, e já gera as parcelas | sim | sim, com as parcelas | sim, só o cadastro | sim, e apaga as parcelas |
| Parcela | não (só nasce com o lançamento) | não (fica dentro do lançamento) | sim | sim | não |

Categoria, centro, pessoa e forma de pagamento usam `PROTECT`. Excluir um lançamento apaga as parcelas porque a chave é `CASCADE`.

## Lançamento e parcelas

- Todo lançamento tem no mínimo 1 parcela. À vista, débito e crédito em uma vez usam 1.
- Com mais de uma parcela, o intervalo em dias é obrigatório.
- O valor líquido é `valor − desconto + acréscimo` e precisa ser maior que zero.
- A divisão usa duas casas. A última parcela fica com o centavo que sobra, para a soma fechar o total.
- O líquido precisa cobrir pelo menos R$ 0,01 em cada parcela.
- Na criação, cada parcela copia a forma de pagamento do lançamento. Na edição da parcela dá para trocar (por exemplo, o lançamento é cartão e uma parcela foi paga no Pix).
- Editar o lançamento não recalcula parcelas nem mexe em valor, quantidade ou vencimentos. Isso preserva o que já foi pago. Para mudar o plano, exclua o lançamento e cadastre de novo.
- Quitar uma parcela exige valor pago e data de pagamento juntos. Os dois em branco significa que ainda está em aberto.

## Campos do lançamento

- `numero`: número da nota, boleto ou documento (texto, opcional).
- `centro`: centro de lançamento opcional, para acompanhar viagem, reforma ou projeto. Pode ser inativado, como categoria, pessoa e forma de pagamento.
- `declara_ir`: marca o lançamento que deve entrar no imposto de renda.
- `agrupado`: marca o lançamento que junta várias notas em um só.
- Lançamento e parcela não têm "ativo". Para desfazer, exclua o lançamento.
- O CPF ou CNPJ da pessoa é único por usuário, não no sistema todo.

## Forma de pagamento

Cadastro simples: nome, descrição e ativo. Exemplos: Pix, boleto, cartão de crédito, cartão de débito, dinheiro, transferência.

## Telas

O visual do app é o template AnotAI (`static/css/financeiro.css` e `financeiro/templates/financeiro/base.html`).

Os botões usam as classes do Bootstrap (`btn-primary`, `btn-outline-primary`, `btn-outline-secondary`, `btn-danger`, `btn-outline-danger`). As cores dessas classes estão sobrescritas no CSS do AnotAI (azul-petróleo, verde de receita, laranja de despesa).

Exclusão pede confirmação com Bootbox (título, mensagem com o nome do registro, "Sim, excluir" e "Cancelar") e só então envia o POST.

Layout com navbar fixa no topo (`base.html`, sem barra lateral). Paleta "Ledger" (azul-petróleo, formal) em `static/css/financeiro.css`, com as cores entrando pelas variáveis `--bs-*` do Bootstrap 5.3. Fonte: IBM Plex Sans. Verde-água e salmão são as cores de receita e despesa, e sempre vêm com ícone e texto (daltonismo).

Situação da parcela tem selo padrão (tag `situacao_parcela` em `fin_tags.py`): paga (verde-água, `success`), em aberto (azul, `info`), vence hoje (âmbar, `warning`) e vencida (salmão, `danger`). O lançamento usa `situacao_lancamento`: quitado, em aberto ou parcela vencida.

Listagens usam django-filter (`financeiro/filters.py` e `form-filter.html`) e a paginação do Django (`paginacao.html`). As tabelas usam DataTables Responsive (`static/js/tabelas.js`, classe `js-tabela`) só para esconder colunas no celular, sem rolagem horizontal. Busca, ordenação e paginação continuam no servidor. Use `data-priority` nos `th` e a classe `all` na coluna de ações; a primeira coluna é a que ganha o botão "+".

Todo botão que envia algo mostra spinner e bloqueia duplo envio, e volta ao normal ao navegar, voltar ou falhar. O padrão está em `static/js/carregando.js` e descrito no skill `.claude/skills/botoes-carregando`. Formulários usam o partial `financeiro/_form-acoes.html` (Cancelar à esquerda, ação principal à direita; no celular a principal vem primeiro).

Valores monetários nunca ficam em preto: receita em verde, despesa em laranja, saldo verde se positivo e laranja se negativo (classes `text-receita`, `text-despesa`, `fin-positive`, `fin-negative`).

## Dados de exemplo

Com o usuário `admin` já criado:

```bash
python manage.py popular_financeiro
```

O comando é idempotente: não duplica lançamento com a mesma descrição para o admin. Os testes rodam em SQLite em memória e não usam o banco de desenvolvimento.
