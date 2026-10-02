---
name: kpi-cards
description: Use sempre que criar ou editar cards KPI/indicadores em dashboards ou listagens para que cada card leve à listagem dos registros que representa, usando os filtros corretos já existentes ou adicionando-os quando necessário.
---

# Cards KPI filtráveis

Cards que representam um conjunto de registros devem funcionar como atalhos para consultar esse mesmo conjunto na listagem correspondente.

## Procedimento

1. Identifique de onde vêm o valor e o rótulo do card. Consulte a view e o queryset que calculam o indicador para determinar quais registros ele representa.
2. Encontre a listagem correspondente, sua rota e seu `FilterSet`. Confirme quais nomes de filtros e valores são aceitos; não deduza parâmetros apenas pelo texto do card.
3. Escolha o destino com base no significado real do indicador. Por exemplo, confirme no modelo e nas opções do filtro qual valor significa receita e qual significa despesa antes de gerar o link. Não copie exemplos sem verificar o domínio do projeto.
4. Se a listagem ainda não oferecer o filtro necessário, implemente-o no `FilterSet` e preserve o escopo de acesso por usuário já aplicado pela view. Não contorne filtros nem exponha registros de outras contas.
5. Faça o card inteiro ser um link acessível para a listagem filtrada. Preserve o visual do projeto, inclua foco visível e não coloque botões ou outros links dentro desse link.
6. Verifique que o conjunto exibido no destino corresponde ao indicador, inclusive limites de datas e estados como pago, aberto ou vencido. Quando o card não identificar um conjunto de registros de forma inequívoca, esclareça o critério antes de inventar um filtro.

## Validação

- Teste a URL gerada pelo card e confirme que ela seleciona o filtro correto.
- Teste os registros incluídos e excluídos pelo filtro, incluindo limites relevantes do indicador.
- Confirme que a listagem continua restrita aos dados do usuário autenticado e que limpar os filtros volta à listagem sem filtros.
- Confirme que a paginação mantém os filtros ativos na URL.