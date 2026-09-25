import django_filters

from .models import Categoria, Lancamento, Pessoa


class CategoriaFilter(django_filters.FilterSet):
    class Meta:
        model = Categoria
        fields = {
            'nome': ['icontains'],
            'descricao': ['icontains'],
            'status': ['exact'],
        }


class PessoaFilter(django_filters.FilterSet):
    class Meta:
        model = Pessoa
        fields = {
            'nome': ['icontains'],
            'documento': ['icontains'],
            'cidade': ['icontains'],
            'status': ['exact'],
        }


class LancamentoFilter(django_filters.FilterSet):
    categoria = django_filters.CharFilter(
        field_name='categoria__nome',
        lookup_expr='icontains',
        label='Categoria contém',
    )
    pessoa = django_filters.CharFilter(
        field_name='pessoa__nome',
        lookup_expr='icontains',
        label='Pessoa contém',
    )
    data = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={'type': 'date'}),
        label='Data do lançamento entre',
    )

    class Meta:
        model = Lancamento
        fields = {
            'descricao': ['icontains'],
            'categoria': ['exact'],
            'pessoa': ['exact'],
            'tipo': ['exact'],
            'data': ['exact'],
            'valor': ['gte', 'lte'],
            'status': ['exact'],
        }