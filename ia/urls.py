from django.urls import path

from . import views

app_name = 'ia'

urlpatterns = [
    path('requisicoes/', views.RequisicaoIAList.as_view(), name='requisicao-list'),
    path('requisicoes/<int:pk>/', views.RequisicaoIADetail.as_view(), name='requisicao-detail'),
    path('meu-consumo/', views.MeuConsumo.as_view(), name='meu-consumo'),
    path('configuracao/', views.ConfiguracaoIAUpdate.as_view(), name='configuracao'),
    path('configuracao/testar-conexao/', views.TestarConexao.as_view(), name='configuracao-testar'),
    path('usuarios/', views.UsuarioIAList.as_view(), name='usuario-list'),
    path('usuarios/<int:usuario_id>/editar/', views.UsuarioIAUpdate.as_view(), name='usuario-update'),
    path('usuarios/<int:usuario_id>/voltar-ao-padrao/', views.UsuarioIAVoltarPadrao.as_view(), name='usuario-resetar'),
    path('manutencao/', views.manutencao, name='manutencao'),
]
