from django.views.generic import CreateView
# Buscar a rota da url pelo name dela (urls.py)
from django.urls import reverse_lazy

from .models import Campus, Jogador, Modalidade, Etapa, Campeonato, Inscricao, Jogo


class CampusCreate(CreateView):
    model = Campus
    fields = ['nome']
    template_name = 'campeonato/form.html'
    success_url = reverse_lazy('index')
    extra_context = {
        'titulo': 'Cadastro de Campus',
        'botao': 'Criar Campus'
    }

#########################################################


class ModalidadeCreate(CreateView):
    model = Modalidade
    fields = ['nome']
    template_name = 'campeonato/form.html'
    success_url = reverse_lazy('index')
    extra_context = {
        'titulo': 'Cadastro de Modalidade',
        'botao': 'Criar Modalidade'
    }

#########################################################


class EtapaCreate(CreateView):
    model = Etapa
    fields = ['nome', 'sequencia', 'quantidade_jogos']
    template_name = 'campeonato/form.html'
    success_url = reverse_lazy('index')
    extra_context = {
        'titulo': 'Cadastro de Etapa',
        'botao': 'Criar Etapa'
    }

##########################################################


class CampeonatoCreate(CreateView):
    model = Campeonato
    fields = ['nome', 'campus', 'data', 'data_inscricao', 'modalidades', 'cadastrado_por']
    template_name = 'campeonato/form.html'
    success_url = reverse_lazy('index')
    extra_context = {
        'titulo': 'Cadastro de Campeonato',
        'botao': 'Criar Campeonato'
    }
