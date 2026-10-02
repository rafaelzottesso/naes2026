from django.urls import path

from .views import (
    CategoriaCreate, CategoriaUpdate, CategoriaDelete, CategoriaList, CategoriaDetail,
    CentroCreate, CentroUpdate, CentroDelete, CentroList, CentroDetail,
    PessoaCreate, PessoaUpdate, PessoaDelete, PessoaList, PessoaDetail,
    FormaPagamentoCreate, FormaPagamentoUpdate, FormaPagamentoDelete,
    FormaPagamentoList, FormaPagamentoDetail,
    LancamentoCreate, LancamentoUpdate, LancamentoDelete, LancamentoList, LancamentoDetail,
    ParcelaUpdate, ParcelaDetail, ParcelaList,
    FinanceiroDashboard,
)


urlpatterns = [
    path('', FinanceiroDashboard.as_view(), name='financeiro-dashboard'),

    path('cadastrar/categoria/', CategoriaCreate.as_view(), name='categoria-create'),
    path('atualizar/categoria/<int:pk>/', CategoriaUpdate.as_view(), name='categoria-update'),
    path('excluir/categoria/<int:pk>/', CategoriaDelete.as_view(), name='categoria-delete'),
    path('listar/categoria/', CategoriaList.as_view(), name='categoria-list'),
    path('detalhar/categoria/<int:pk>/', CategoriaDetail.as_view(), name='categoria-detail'),

    path('cadastrar/centro/', CentroCreate.as_view(), name='centro-create'),
    path('atualizar/centro/<int:pk>/', CentroUpdate.as_view(), name='centro-update'),
    path('excluir/centro/<int:pk>/', CentroDelete.as_view(), name='centro-delete'),
    path('listar/centro/', CentroList.as_view(), name='centro-list'),
    path('detalhar/centro/<int:pk>/', CentroDetail.as_view(), name='centro-detail'),

    path('cadastrar/pessoa/', PessoaCreate.as_view(), name='pessoa-create'),
    path('atualizar/pessoa/<int:pk>/', PessoaUpdate.as_view(), name='pessoa-update'),
    path('excluir/pessoa/<int:pk>/', PessoaDelete.as_view(), name='pessoa-delete'),
    path('listar/pessoa/', PessoaList.as_view(), name='pessoa-list'),
    path('detalhar/pessoa/<int:pk>/', PessoaDetail.as_view(), name='pessoa-detail'),

    path('cadastrar/forma-pagamento/', FormaPagamentoCreate.as_view(), name='forma-pagamento-create'),
    path('atualizar/forma-pagamento/<int:pk>/', FormaPagamentoUpdate.as_view(), name='forma-pagamento-update'),
    path('excluir/forma-pagamento/<int:pk>/', FormaPagamentoDelete.as_view(), name='forma-pagamento-delete'),
    path('listar/forma-pagamento/', FormaPagamentoList.as_view(), name='forma-pagamento-list'),
    path('detalhar/forma-pagamento/<int:pk>/', FormaPagamentoDetail.as_view(), name='forma-pagamento-detail'),

    path('cadastrar/lancamento/', LancamentoCreate.as_view(), name='lancamento-create'),
    path('atualizar/lancamento/<int:pk>/', LancamentoUpdate.as_view(), name='lancamento-update'),
    path('excluir/lancamento/<int:pk>/', LancamentoDelete.as_view(), name='lancamento-delete'),
    path('listar/lancamento/', LancamentoList.as_view(), name='lancamento-list'),
    path('detalhar/lancamento/<int:pk>/', LancamentoDetail.as_view(), name='lancamento-detail'),

    path('atualizar/parcela/<int:pk>/', ParcelaUpdate.as_view(), name='parcela-update'),
    path('detalhar/parcela/<int:pk>/', ParcelaDetail.as_view(), name='parcela-detail'),
    path('listar/parcela/', ParcelaList.as_view(), name='parcela-list'),
]
