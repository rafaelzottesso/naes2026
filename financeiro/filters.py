import django_filters

from .models import TIPO_LANCAMENTO, Categoria, FormaPagamento, Lancamento, Pessoa


class CategoriaFilter(django_filters.FilterSet):
    nome = django_filters.CharFilter(lookup_expr='icontains', label='Nome contém')
    descricao = django_filters.CharFilter(lookup_expr='icontains', label='Descrição contém')
    status = django_filters.BooleanFilter(label='Ativo')

    class Meta:
        model = Categoria
        fields = []


class PessoaFilter(django_filters.FilterSet):
    nome = django_filters.CharFilter(lookup_expr='icontains', label='Nome contém')
    documento = django_filters.CharFilter(lookup_expr='icontains', label='CPF ou CNPJ contém')
    cidade = django_filters.CharFilter(lookup_expr='icontains', label='Cidade contém')
    status = django_filters.BooleanFilter(label='Ativo')

    class Meta:
        model = Pessoa
        fields = []


class FormaPagamentoFilter(django_filters.FilterSet):
    nome = django_filters.CharFilter(lookup_expr='icontains', label='Nome contém')
    descricao = django_filters.CharFilter(lookup_expr='icontains', label='Descrição contém')
    status = django_filters.BooleanFilter(label='Ativo')

    class Meta:
        model = FormaPagamento
        fields = []


class LancamentoFilter(django_filters.FilterSet):
    descricao = django_filters.CharFilter(lookup_expr='icontains', label='Descrição contém')
    categoria = django_filters.ModelChoiceFilter(
        queryset=lambda request: Categoria.objects.filter(criado_por=request.user).order_by('nome'),
        label='Categoria',
    )
    pessoa = django_filters.ModelChoiceFilter(
        queryset=lambda request: Pessoa.objects.filter(criado_por=request.user).order_by('nome'),
        label='Cliente/Fornecedor',
    )
    forma_pagamento = django_filters.ModelChoiceFilter(
        queryset=lambda request: FormaPagamento.objects.filter(criado_por=request.user).order_by('nome'),
        label='Forma de pagamento',
    )
    tipo = django_filters.ChoiceFilter(choices=TIPO_LANCAMENTO, label='Tipo')
    data = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={'type': 'date'}),
        label='Data da primeira parcela entre',
    )
    valor_min = django_filters.NumberFilter(field_name='valor', lookup_expr='gte', label='Valor mínimo')
    valor_max = django_filters.NumberFilter(field_name='valor', lookup_expr='lte', label='Valor máximo')
    status = django_filters.BooleanFilter(label='Ativo')

    class Meta:
        model = Lancamento
        fields = []
