
from django.urls import path
from .views import CampusCreate, ModalidadeCreate, EtapaCreate, CampeonatoCreate

urlpatterns = [
    path('cadastrar/campus/', CampusCreate.as_view(), name='campus-create'),
    path('cadastrar/modalidade/', ModalidadeCreate.as_view(), name='modalidade-create'),
    path('cadastrar/etapa/', EtapaCreate.as_view(), name='etapa-create'),
    path('cadastrar/campeonato/', CampeonatoCreate.as_view(), name='campeonato-create'),
]
