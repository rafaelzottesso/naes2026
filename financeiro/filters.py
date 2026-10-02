import django_filters
from django.utils import timezone

from .models import TIPO_LANCAMENTO, Categoria, Centro, FormaPagamento, Lancamento, Parcela, Pessoa


class CategoriaFilter(django_filters.FilterSet):
    nome = django_filters.CharFilter(lookup_expr='icontains', label='Nome contém')
    descricao = django_filters.CharFilter(lookup_expr='icontains', label='Descrição contém')
    status = django_filters.BooleanFilter(label='Ativo')

    class Meta:
        model = Categoria
        fields = []


class CentroFilter(django_filters.FilterSet):
    nome = django_filters.CharFilter(lookup_expr='icontains', label='Nome contém')
    descricao = django_filters.CharFilter(lookup_expr='icontains', label='Descrição contém')
    status = django_filters.BooleanFilter(label='Ativo')

    class Meta:
        model = Centro
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
    numero = django_filters.CharFilter(lookup_expr='icontains', label='Número contém')
    categoria = django_filters.ModelChoiceFilter(
        queryset=lambda request: Categoria.objects.filter(criado_por=request.user).order_by('nome'),
        label='Categoria',
    )
    centro = django_filters.ModelChoiceFilter(
        queryset=lambda request: Centro.objects.filter(criado_por=request.user).order_by('nome'),
        label='Centro de lançamento',
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
    declara_ir = django_filters.BooleanFilter(label='Declara no imposto de renda')
    agrupado = django_filters.BooleanFilter(label='Lançamento agrupado')

    class Meta:
        model = Lancamento
        fields = []


class ParcelaFilter(django_filters.FilterSet):
    descricao = django_filters.CharFilter(
        field_name='lancamento__descricao', lookup_expr='icontains', label='Lançamento contém',
    )
    categoria = django_filters.ModelChoiceFilter(
        field_name='lancamento__categoria',
        queryset=lambda request: Categoria.objects.filter(criado_por=request.user).order_by('nome'),
        label='Categoria',
    )
    pessoa = django_filters.ModelChoiceFilter(
        field_name='lancamento__pessoa',
        queryset=lambda request: Pessoa.objects.filter(criado_por=request.user).order_by('nome'),
        label='Cliente/Fornecedor',
    )
    forma_pagamento = django_filters.ModelChoiceFilter(
        queryset=lambda request: FormaPagamento.objects.filter(criado_por=request.user).order_by('nome'),
        label='Forma de pagamento',
    )
    tipo = django_filters.ChoiceFilter(field_name='lancamento__tipo', choices=TIPO_LANCAMENTO, label='Tipo')
    data = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={'type': 'date'}),
        label='Vencimento entre',
    )
    situacao = django_filters.ChoiceFilter(
        choices=(('pagas', 'Pagas'), ('abertas', 'Em aberto')),
        method='filtrar_situacao',
        label='Situação',
    )
    vencidas = django_filters.BooleanFilter(method='filtrar_vencidas', label='Somente vencidas e não pagas')

    class Meta:
        model = Parcela
        fields = []

    def filtrar_situacao(self, queryset, name, value):
        if value == 'pagas':
            return queryset.filter(data_pagamento__isnull=False, valor_pago__isnull=False)
        if value == 'abertas':
            return queryset.filter(
                data__gte=timezone.localdate(),
                data_pagamento__isnull=True,
                valor_pago__isnull=True,
            )
        return queryset

    def filtrar_vencidas(self, queryset, name, value):
        if value:
            return queryset.filter(
                data__lt=timezone.localdate(),
                data_pagamento__isnull=True,
                valor_pago__isnull=True,
            )
        return queryset
