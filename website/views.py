from django.views.generic import TemplateView
from financeiro.models import Lancamento, Categoria, Pessoa
from django.db.models import Sum


class IndexView(TemplateView):
    template_name = "website/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["total_lancamentos"] = Lancamento.objects.count()
        context["total_categorias"] = Categoria.objects.count()
        context["total_pessoas"] = Pessoa.objects.count()
        context["ultimos_lancamentos"] = Lancamento.objects.select_related('categoria', 'pessoa').order_by("-data")[:5]

        return context