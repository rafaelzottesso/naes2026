import django_filters
from django.contrib.auth import get_user_model

from .models import RequisicaoIA


class RequisicaoIAFilter(django_filters.FilterSet):
    usuario = django_filters.ModelChoiceFilter(
        queryset=get_user_model().objects.order_by('username'),
        label='Usuário',
    )
    situacao = django_filters.ChoiceFilter(choices=RequisicaoIA.SITUACOES, label='Situação')
    resultado = django_filters.ChoiceFilter(
        choices=[('erro', 'Somente com erro')],
        method='filtrar_resultado',
        label='Resultado',
    )
    finalidade = django_filters.CharFilter(lookup_expr='icontains', label='Finalidade contém')
    origem = django_filters.ChoiceFilter(choices=RequisicaoIA.ORIGENS, label='Origem')
    periodo = django_filters.DateFromToRangeFilter(
        field_name='criado_em__date',
        widget=django_filters.widgets.DateRangeWidget(attrs={'type': 'date'}),
        label='Criado entre',
    )

    class Meta:
        model = RequisicaoIA
        fields = []

    def filtrar_resultado(self, queryset, name, value):
        if value == 'erro':
            return queryset.exclude(situacao='sucesso')
        return queryset
