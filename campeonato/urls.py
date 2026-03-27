
from django.urls import path
from .views import (
    CampusCreate, CampusUpdate, CampusDelete, CampusList, CampusDetail,
    ModalidadeCreate, ModalidadeUpdate, ModalidadeDelete, ModalidadeList, ModalidadeDetail,
    EtapaCreate, EtapaUpdate, EtapaDelete, EtapaList, EtapaDetail,
    JogadorCreate, JogadorUpdate, JogadorDelete, JogadorList, JogadorDetail,
    CampeonatoCreate, CampeonatoUpdate, CampeonatoDelete, CampeonatoList, CampeonatoDetail,
    InscricaoCreate, InscricaoUpdate, InscricaoDelete, InscricaoList, InscricaoDetail,
    JogoCreate, JogoUpdate, JogoDelete, JogoList, JogoDetail,
)


urlpatterns = [
    path('cadastrar/campus/', CampusCreate.as_view(), name='campus-create'),
    path('atualizar/campus/<int:pk>/', CampusUpdate.as_view(), name='campus-update'),
    path('excluir/campus/<int:pk>/', CampusDelete.as_view(), name='campus-delete'),
    path('listar/campus/', CampusList.as_view(), name='campus-list'),
    path('detalhar/campus/<int:pk>/', CampusDetail.as_view(), name='campus-detail'),

    path('cadastrar/modalidade/', ModalidadeCreate.as_view(), name='modalidade-create'),
    path('atualizar/modalidade/<int:pk>/', ModalidadeUpdate.as_view(), name='modalidade-update'),
    path('excluir/modalidade/<int:pk>/', ModalidadeDelete.as_view(), name='modalidade-delete'),
    path('listar/modalidade/', ModalidadeList.as_view(), name='modalidade-list'),
    path('detalhar/modalidade/<int:pk>/', ModalidadeDetail.as_view(), name='modalidade-detail'),

    path('cadastrar/etapa/', EtapaCreate.as_view(), name='etapa-create'),
    path('atualizar/etapa/<int:pk>/', EtapaUpdate.as_view(), name='etapa-update'),
    path('excluir/etapa/<int:pk>/', EtapaDelete.as_view(), name='etapa-delete'),
    path('listar/etapa/', EtapaList.as_view(), name='etapa-list'),
    path('detalhar/etapa/<int:pk>/', EtapaDetail.as_view(), name='etapa-detail'),

    path('cadastrar/jogador/', JogadorCreate.as_view(), name='jogador-create'),
    path('atualizar/jogador/<int:pk>/', JogadorUpdate.as_view(), name='jogador-update'),
    path('excluir/jogador/<int:pk>/', JogadorDelete.as_view(), name='jogador-delete'),
    path('listar/jogador/', JogadorList.as_view(), name='jogador-list'),
    path('detalhar/jogador/<int:pk>/', JogadorDetail.as_view(), name='jogador-detail'),
    
    path('cadastrar/campeonato/', CampeonatoCreate.as_view(), name='campeonato-create'),
    path('atualizar/campeonato/<int:pk>/', CampeonatoUpdate.as_view(), name='campeonato-update'),
    path('excluir/campeonato/<int:pk>/', CampeonatoDelete.as_view(), name='campeonato-delete'),
    path('listar/campeonato/', CampeonatoList.as_view(), name='campeonato-list'),
    path('detalhar/campeonato/<int:pk>/', CampeonatoDetail.as_view(), name='campeonato-detail'),

    path('cadastrar/inscricao/', InscricaoCreate.as_view(), name='inscricao-create'),
    path('atualizar/inscricao/<int:pk>/', InscricaoUpdate.as_view(), name='inscricao-update'),
    path('excluir/inscricao/<int:pk>/', InscricaoDelete.as_view(), name='inscricao-delete'),
    path('listar/inscricao/', InscricaoList.as_view(), name='inscricao-list'),
    path('detalhar/inscricao/<int:pk>/', InscricaoDetail.as_view(), name='inscricao-detail'),

    path('cadastrar/jogo/', JogoCreate.as_view(), name='jogo-create'),
    path('atualizar/jogo/<int:pk>/', JogoUpdate.as_view(), name='jogo-update'),
    path('excluir/jogo/<int:pk>/', JogoDelete.as_view(), name='jogo-delete'),
    path('listar/jogo/', JogoList.as_view(), name='jogo-list'),
    path('detalhar/jogo/<int:pk>/', JogoDetail.as_view(), name='jogo-detail'),
]
