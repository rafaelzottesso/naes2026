import django_filters

from .models import (
    Campus,
    Campeonato,
    Etapa,
    Inscricao,
    Jogador,
    Jogo,
    Modalidade,
)


class CampusFilter(django_filters.FilterSet):
    class Meta:
        model = Campus
        fields = {'nome': ['icontains']}


class ModalidadeFilter(django_filters.FilterSet):
    class Meta:
        model = Modalidade
        fields = {'nome': ['icontains']}


class EtapaFilter(django_filters.FilterSet):
    class Meta:
        model = Etapa
        fields = {
            'nome': ['icontains'],
            'sequencia': ['gte', 'lte'],
            'quantidade_jogos': ['gte', 'lte'],
        }


class JogadorFilter(django_filters.FilterSet):
    campus = django_filters.ModelChoiceFilter(
        queryset=Campus.objects.all(),
        label='Campus',
    )

    class Meta:
        model = Jogador
        fields = {
            'nome': ['icontains'],
            'id_jogador': ['icontains'],
            'campus': ['exact'],
        }


class CampeonatoFilter(django_filters.FilterSet):
    campus = django_filters.ModelChoiceFilter(
        queryset=Campus.objects.all(),
        label='Campus',
    )
    data = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={'type': 'date'}),
        label='Data do campeonato entre',
    )

    class Meta:
        model = Campeonato
        fields = {
            'nome': ['icontains'],
            'campus': ['exact'],
            'data': ['exact'],
        }


class InscricaoFilter(django_filters.FilterSet):
    campeonato = django_filters.CharFilter(
        field_name='campeonato__nome',
        lookup_expr='icontains',
        label='Campeonato contém',
    )
    modalidade = django_filters.ModelChoiceFilter(
        queryset=Modalidade.objects.all(),
        label='Modalidade',
    )
    inscrito_em = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={'type': 'date'}),
        label='Inscrito entre',
    )

    class Meta:
        model = Inscricao
        fields = {
            'nome_time': ['icontains'],
            'campeonato': ['exact'],
            'modalidade': ['exact'],
            'confirmada': ['exact'],
            'inscrito_em': ['exact'],
        }


class JogoFilter(django_filters.FilterSet):
    time_1 = django_filters.CharFilter(
        field_name='time_1__nome_time',
        lookup_expr='icontains',
        label='Time 1 contém',
    )
    time_2 = django_filters.CharFilter(
        field_name='time_2__nome_time',
        lookup_expr='icontains',
        label='Time 2 contém',
    )
    etapa = django_filters.ModelChoiceFilter(
        queryset=Etapa.objects.all(),
        label='Etapa',
    )
    modalidade = django_filters.ModelChoiceFilter(
        queryset=Modalidade.objects.all(),
        label='Modalidade',
    )
    data_hora = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={'type': 'date'}),
        label='Data do jogo entre',
    )

    class Meta:
        model = Jogo
        fields = {
            'time_1': ['exact'],
            'time_2': ['exact'],
            'resultado': ['icontains'],
            'etapa': ['exact'],
            'modalidade': ['exact'],
            'data_hora': ['exact'],
        }