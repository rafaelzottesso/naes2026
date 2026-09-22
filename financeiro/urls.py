from django.urls import path

from .views import (
    CategoriaCreate, CategoriaUpdate, CategoriaDelete, CategoriaList, CategoriaDetail,
    LancamentoCreate, LancamentoUpdate, LancamentoDelete, LancamentoList, LancamentoDetail,
    FinanceiroDashboard,
)


urlpatterns = [
    path('', FinanceiroDashboard.as_view(), name='financeiro-dashboard'),

    path('cadastrar/categoria/', CategoriaCreate.as_view(), name='categoria-create'),
    path('atualizar/categoria/<int:pk>/', CategoriaUpdate.as_view(), name='categoria-update'),
    path('excluir/categoria/<int:pk>/', CategoriaDelete.as_view(), name='categoria-delete'),
    path('listar/categoria/', CategoriaList.as_view(), name='categoria-list'),
    path('detalhar/categoria/<int:pk>/', CategoriaDetail.as_view(), name='categoria-detail'),

    path('cadastrar/lancamento/', LancamentoCreate.as_view(), name='lancamento-create'),
    path('atualizar/lancamento/<int:pk>/', LancamentoUpdate.as_view(), name='lancamento-update'),
    path('excluir/lancamento/<int:pk>/', LancamentoDelete.as_view(), name='lancamento-delete'),
    path('listar/lancamento/', LancamentoList.as_view(), name='lancamento-list'),
    path('detalhar/lancamento/<int:pk>/', LancamentoDetail.as_view(), name='lancamento-detail'),
]
