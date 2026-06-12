from django.views.generic import TemplateView
from campeonato.models import Campeonato

# import timezone do django
from django.utils import timezone


class IndexView(TemplateView):
    template_name = "website/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # pega todos os campeonatos e conta quantos tem e coloca numa lista no contexto
        todos_campeonatos = Campeonato.objects.all()
        # conta quantos campeonatos tem e coloca no contexto o valor inteiro
        context["total_campeonatos"] = todos_campeonatos.count()
        
        # pega os 5 campeonatos mais recentes e coloca numa lista no contexto (LIMITE DE 5)
        campeonatos = todos_campeonatos.order_by("-cadastrado_em")[:5]
        context["ultimos_campeonatos"] = campeonatos

        # Filtrar pela data "greater than" (data_inscricao__gt) a data atual (timezone.now()) para pegar apenas os campeonatos que ainda estão com inscrições abertas
        context["campeonatos_abertos"] = todos_campeonatos.filter(data_inscricao__gt=timezone.now())
        # Contar quantos campeonatos estão com inscrições abertas e colocar no contexto o valor inteiro
        context["total_abertos"] = context["campeonatos_abertos"].count()
        

        return context

class ContatoView(TemplateView):
    template_name = "website/contato.html"
    
class SobreView(TemplateView):
    template_name = "website/sobre.html"