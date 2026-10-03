---
name: listas-financeiro
description: Use sempre que criar ou editar uma view, template ou tela de listagem do financeiro AnotAI para seguir o padrão visual e técnico do LancamentoList, com filtros, três KPIs clicáveis por padrão, tabela responsiva, paginação e consultas eficientes.
---

# Listas do AnotAI

Use `financeiro/templates/financeiro/list/lancamento.html` e `LancamentoList` como referência para as listagens do financeiro. Preserve as particularidades do modelo, sem copiar textos ou filtros que não façam sentido para ele.

## View e consultas

1. Para listagem com filtros, use `FilterView` com `filterset_class`, `paginate_by` e `ordering`. Mantenha os mixins de login e escopo por usuário antes de `FilterView`.
2. Se sobrescrever `get_queryset`, comece por `super().get_queryset()` para preservar o escopo existente. Inclua `select_related` para todas as relações acessadas na tabela; use `prefetch_related` para relações múltiplas.
3. Calcule os valores de KPI no banco com `aggregate`, `Count`, `Sum` e filtros condicionais. Não materialize todos os registros nem some valores em Python para montar os cards.
   Sempre agregue sobre o queryset já filtrado da listagem (`filterset.qs`), preservando o escopo do usuário. Considere todos os resultados filtrados, não apenas a página atual nem todos os registros do período; KPIs e contagem da tabela devem representar o mesmo conjunto.
   Se o queryset tiver anotações que juntem relações múltiplas, evite somar valores do modelo principal diretamente sobre essa junção, pois cada registro pode ser repetido. Agregue os IDs filtrados sobre um queryset sem essas anotações.
4. Use `django-filter` em `financeiro/filters.py`. Confirme os campos e escolhas reais antes de construir filtros ou links; filtros de relações devem limitar as opções aos dados do usuário autenticado.

## Cabeçalho e conteúdo

1. Abra a página com `fin-page-head`: eyebrow curto, `h1` com o nome da lista, descrição breve e `fin-head-actions`.
2. Mantenha a mesma composição de `lancamento.html`: ação secundária `Dashboard` com `btn-outline-secondary` e ação principal para criar o registro (ou o registro pai que o gera) com `btn-primary`.
3. Na sequência, inclua `financeiro/form-filter.html`, três KPIs por padrão e então a listagem em `fin-panel`. Use o título e a contagem do conjunto filtrado no cabeçalho do painel.
4. Toda listagem tem três cards KPI por padrão. Cada card comunica rótulo, valor e, quando útil, quantidade; o card inteiro é um link acessível para a lista filtrada dos registros que representa. Só altere essa quantidade quando a tarefa pedir outra explicitamente.
5. Consulte a skill `kpi-cards` para derivar cada destino dos filtros reais. Não invente nomes/valores de parâmetros nem associe um indicador ao conjunto errado. Não coloque links ou botões dentro do link do card.

## Tabela, estados e paginação

1. Siga o padrão AnotAI observado em `lancamento.html`: contêiner `fin-table-wrap`, tabela `table fin-table align-middle js-tabela`, cabeçalhos em português e prioridades `data-priority` para responsividade. Use `all` na coluna de ações.
2. Use `data-order` com valores não localizados em datas, números e moeda, para a ordenação refletir o valor real e não a formatação brasileira.
3. Cada linha tem uma célula por cabeçalho. Ações ficam na coluna final; aproveite os estilos e menus existentes.
4. Mostre estado vazio fora da tabela, sem linha com `colspan` no `tbody`.
5. Inclua `financeiro/paginacao.html` após a listagem. Preserve os filtros na URL ao navegar e mantenha o botão “Limpar” voltando à rota sem parâmetros.

## Validação

- Teste filtros, paginação e escopo do usuário, inclusive os links dos três KPIs.
- Confira contagens e valores dos cards frente aos registros que cada filtro retorna.
- Verifique que a tabela renderiza as relações sem consultas repetidas e que `manage.py test` e `manage.py check` passam.