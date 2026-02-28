
from django.urls import path
from .views import IndexView, ContatoView

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("contato/", ContatoView.as_view(), name="contato"),
]
