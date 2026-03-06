from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = "website/index.html"

class ContatoView(TemplateView):
    template_name = "website/contato.html"
    
class SobreView(TemplateView):
    template_name = "website/sobre.html"