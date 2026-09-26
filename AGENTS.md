# Fluxo — finanças pessoais

Projeto Django de controle financeiro pessoal. Cada usuário vê e altera só o que ele mesmo cadastrou (`criado_por`). O Django Admin continua enxergando tudo.

## Modelos e o que cada um pode fazer

| Modelo | Criar | Listar | Ver | Editar | Excluir |
| --- | --- | --- | --- | --- | --- |
| Categoria | sim | sim | sim | sim | sim, se nenhum lançamento usar |
| Pessoa | sim | sim | sim | sim | sim, se nenhum lançamento usar |
| Forma de pagamento | sim | sim | sim | sim | sim, se nenhum lançamento ou parcela usar |
| Lançamento | sim, e já gera as parcelas | sim | sim, com as parcelas | sim, só o cadastro | sim, e apaga as parcelas |
| Parcela | não (só nasce com o lançamento) | não (fica dentro do lançamento) | sim | sim | não |

Categoria, pessoa e forma de pagamento usam `PROTECT`. Excluir um lançamento apaga as parcelas porque a chave é `CASCADE`.

## Lançamento e parcelas

- Todo lançamento tem no mínimo 1 parcela. À vista, débito e crédito em uma vez usam 1.
- Com mais de uma parcela, o intervalo em dias é obrigatório.
- O valor líquido é `valor − desconto + acréscimo` e precisa ser maior que zero.
- A divisão usa duas casas. A última parcela fica com o centavo que sobra, para a soma fechar o total.
- O líquido precisa cobrir pelo menos R$ 0,01 em cada parcela.
- Na criação, cada parcela copia a forma de pagamento do lançamento. Na edição da parcela dá para trocar (por exemplo, o lançamento é cartão e uma parcela foi paga no Pix).
- Editar o lançamento não recalcula parcelas nem mexe em valor, quantidade ou vencimentos. Isso preserva o que já foi pago. Para mudar o plano, exclua o lançamento e cadastre de novo.
- Quitar uma parcela exige valor pago e data de pagamento juntos. Os dois em branco significa que ainda está em aberto.

## Forma de pagamento

Cadastro simples: nome, descrição e ativo. Exemplos: Pix, boleto, cartão de crédito, cartão de débito, dinheiro, transferência.

## Telas

O visual do app é o template Fluxo (`static/css/financeiro.css` e `financeiro/templates/financeiro/base.html`).

Os botões usam as classes do Bootstrap (`btn-primary`, `btn-outline-primary`, `btn-outline-secondary`, `btn-danger`, `btn-outline-danger`). As cores dessas classes estão sobrescritas no CSS do Fluxo (verde-petróleo, verde de receita, vermelho de despesa).

Exclusão pede confirmação com Bootbox (título, mensagem com o nome do registro, "Sim, excluir" e "Cancelar") e só então envia o POST.

Listagens usam django-filter (`financeiro/filters.py` e `form-filter.html`) e a paginação do Django (`paginacao.html`). A tabela do Fluxo tem versão em cards no celular, então estas listas não usam DataTables.

## Dados de exemplo

Com o usuário `admin` já criado:

```bash
python manage.py popular_financeiro
```

O comando é idempotente: não duplica lançamento com a mesma descrição para o admin. Os testes rodam em SQLite em memória e não usam o banco de desenvolvimento.
