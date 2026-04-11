from django.views.generic import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

# Buscar a rota da url pelo name dela (urls.py)
from django.urls import reverse_lazy

from .models import Campus, Jogador, Modalidade, Etapa, Campeonato, Inscricao, Jogo


class CampusCreate(CreateView):
    model = Campus
    fields = ['nome']
    template_name = 'campeonato/form.html'
    success_url = reverse_lazy('campus-list')
    extra_context = {
        'titulo': 'Cadastro de Campus',
        'botao': 'Criar Campus'
    }


class CampusUpdate(UpdateView):
    model = Campus
    fields = ['nome']
    template_name = 'campeonato/form.html'
    success_url = reverse_lazy('campus-list')
    extra_context = {
        'titulo': 'Editar dados do Campus',
        'botao': 'Atualizar Campus'
    }


class CampusDelete(DeleteView):
    model = Campus
    template_name = 'campeonato/form.html'
    success_url = reverse_lazy('campus-list')
    extra_context = {
        'titulo': 'Excluir Campus',
        'botao': 'Sim, excluir!'
    }


class CampusList(ListView):
    model = Campus
    template_name = 'campeonato/list/campus.html'
    paginate_by = 20


class CampusDetail(DetailView):
    model = Campus
    template_name = 'campeonato/detail/campus.html'



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


class ModalidadeUpdate(UpdateView):
    model = Modalidade
    fields = ['nome']
    template_name = 'campeonato/form.html'
    success_url = reverse_lazy('index')
    extra_context = {
        'titulo': 'Editar dados da Modalidade',
        'botao': 'Atualizar Modalidade'
    }


class ModalidadeDelete(DeleteView):
    model = Modalidade
    template_name = 'campeonato/form.html'
    success_url = reverse_lazy('index')
    extra_context = {
        'titulo': 'Excluir Modalidade',
        'botao': 'Sim, excluir!'
    }


class ModalidadeList(ListView):
    model = Modalidade
    template_name = 'campeonato/list/modalidade.html'


class ModalidadeDetail(DetailView):
    model = Modalidade
    template_name = 'campeonato/detail/modalidade.html'

#########################################################


class EtapaCreate(CreateView):
    model = Etapa
    fields = ['nome', 'sequencia', 'quantidade_jogos']
    template_name = 'campeonato/form.html'
    success_url = reverse_lazy('index')
    extra_context = {
        'titulo': 'Cadastro de Etapa',
        'botao': 'Criar Etapa',
        'largura': 8
    }


class EtapaUpdate(UpdateView):
    model = Etapa
    fields = ['nome', 'sequencia', 'quantidade_jogos']
    template_name = 'campeonato/form.html'
    success_url = reverse_lazy('index')
    extra_context = {
        'titulo': 'Editar dados da Etapa',
        'botao': 'Atualizar Etapa'
    }


class EtapaDelete(DeleteView):
    model = Etapa
    template_name = 'campeonato/form.html'
    success_url = reverse_lazy('index')
    extra_context = {
        'titulo': 'Excluir Etapa',
        'botao': 'Sim, excluir!'
    }


class EtapaList(ListView):
    model = Etapa
    template_name = 'campeonato/list/etapa.html'


class EtapaDetail(DetailView):
    model = Etapa
    template_name = 'campeonato/detail/etapa.html'


class JogadorCreate(CreateView):
    model = Jogador
    fields = ['nome', 'id_jogador', 'campus', 'usuario']
    template_name = 'campeonato/form.html'
    success_url = reverse_lazy('index')
    extra_context = {
        'titulo': 'Cadastro de Jogador',
        'botao': 'Criar Jogador'
    }


class JogadorUpdate(UpdateView):
    model = Jogador
    fields = ['nome', 'id_jogador', 'campus', 'usuario']
    template_name = 'campeonato/form.html'
    success_url = reverse_lazy('index')
    extra_context = {
        'titulo': 'Editar dados do Jogador',
        'botao': 'Atualizar Jogador'
    }


class JogadorDelete(DeleteView):
    model = Jogador
    template_name = 'campeonato/form.html'
    success_url = reverse_lazy('index')
    extra_context = {
        'titulo': 'Excluir Jogador',
        'botao': 'Sim, excluir!'
    }


class JogadorList(ListView):
    model = Jogador
    template_name = 'campeonato/list/jogador.html'


class JogadorDetail(DetailView):
    model = Jogador
    template_name = 'campeonato/detail/jogador.html'

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


class CampeonatoUpdate(UpdateView):
    model = Campeonato
    fields = ['nome', 'campus', 'data', 'data_inscricao', 'modalidades', 'cadastrado_por']
    template_name = 'campeonato/form.html'
    success_url = reverse_lazy('index')
    extra_context = {
        'titulo': 'Editar dados do Campeonato',
        'botao': 'Atualizar Campeonato'
    }


class CampeonatoDelete(DeleteView):
    model = Campeonato
    template_name = 'campeonato/form.html'
    success_url = reverse_lazy('index')
    extra_context = {
        'titulo': 'Excluir Campeonato',
        'botao': 'Sim, excluir!'
    }


class CampeonatoList(ListView):
    model = Campeonato
    template_name = 'campeonato/list/campeonato.html'


class CampeonatoDetail(DetailView):
    model = Campeonato
    template_name = 'campeonato/detail/campeonato.html'


class InscricaoCreate(CreateView):
    model = Inscricao
    fields = ['nome_time', 'jogadores', 'campeonato', 'modalidade', 'inscrito_por']
    template_name = 'campeonato/form.html'
    success_url = reverse_lazy('index')
    extra_context = {
        'titulo': 'Cadastro de Inscrição',
        'botao': 'Criar Inscrição'
    }


class InscricaoUpdate(UpdateView):
    model = Inscricao
    fields = ['nome_time', 'jogadores', 'campeonato', 'modalidade', 'confirmada', 'confirmada_em', 'inscrito_por']
    template_name = 'campeonato/form.html'
    success_url = reverse_lazy('index')
    extra_context = {
        'titulo': 'Editar dados da Inscrição',
        'botao': 'Atualizar Inscrição'
    }


class InscricaoDelete(DeleteView):
    model = Inscricao
    template_name = 'campeonato/form.html'
    success_url = reverse_lazy('index')
    extra_context = {
        'titulo': 'Excluir Inscrição',
        'botao': 'Sim, excluir!'
    }


class InscricaoList(ListView):
    model = Inscricao
    template_name = 'campeonato/list/inscricao.html'


class InscricaoDetail(DetailView):
    model = Inscricao
    template_name = 'campeonato/detail/inscricao.html'


class JogoCreate(CreateView):
    model = Jogo
    fields = ['time_1', 'time_2', 'data_hora', 'etapa', 'modalidade', 'vencedor', 'resultado', 'cadastrado_por']
    template_name = 'campeonato/form.html'
    success_url = reverse_lazy('index')
    extra_context = {
        'titulo': 'Cadastro de Jogo',
        'botao': 'Criar Jogo'
    }


class JogoUpdate(UpdateView):
    model = Jogo
    fields = ['time_1', 'time_2', 'data_hora', 'etapa', 'modalidade', 'vencedor', 'resultado', 'cadastrado_por']
    template_name = 'campeonato/form.html'
    success_url = reverse_lazy('index')
    extra_context = {
        'titulo': 'Editar dados do Jogo',
        'botao': 'Atualizar Jogo'
    }


class JogoDelete(DeleteView):
    model = Jogo
    template_name = 'campeonato/form.html'
    success_url = reverse_lazy('index')
    extra_context = {
        'titulo': 'Excluir Jogo',
        'botao': 'Sim, excluir!'
    }


class JogoList(ListView):
    model = Jogo
    template_name = 'campeonato/list/jogo.html'


class JogoDetail(DetailView):
    model = Jogo
    template_name = 'campeonato/detail/jogo.html'
