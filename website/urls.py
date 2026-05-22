
from django.urls import path
from .views import IndexView, ContatoView, SobreView

# Importas as views para gerenciamento de usuários
from django.contrib.auth.views import (
    LoginView,
    LogoutView, 
    PasswordChangeView,
)

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("contato/", ContatoView.as_view(), name="contato"),
    path("sobre/", SobreView.as_view(), name="sobre"),

    # URL para login e usuários reutiliza o meu template de form e recebe o texto do titulo e botão
    path("login/", LoginView.as_view(
            template_name="campeonato/form.html",
            extra_context = {
                'titulo': 'Autenticação de Usuário',
                'botao': 'Entrar'
            }
        ), name="login"),

    # a URL de logout não precisa de template
    path("logout/", LogoutView.as_view(), name="logout"),
    
    # URL para login e usuários reutiliza o meu template de form e recebe o texto do titulo e botão    
    path("alterar-senha/", PasswordChangeView.as_view(
            template_name="campeonato/form.html",
            extra_context = {
                'titulo': 'Alterar minha senha',
                'botao': 'Alterar Senha'
            }
        ), name="alterar-senha"),
]
