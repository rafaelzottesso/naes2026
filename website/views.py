from django.views.generic import TemplateView
from financeiro.models import Lancamento, Categoria, Pessoa, FormaPagamento


class IndexView(TemplateView):
    template_name = "website/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario = self.request.user

        if usuario.is_authenticated:
            lancamentos = Lancamento.objects.filter(criado_por=usuario)
            context["total_lancamentos"] = lancamentos.count()
            context["total_categorias"] = Categoria.objects.filter(criado_por=usuario).count()
            context["total_pessoas"] = Pessoa.objects.filter(criado_por=usuario).count()
            context["total_formas"] = FormaPagamento.objects.filter(criado_por=usuario).count()
            context["ultimos_lancamentos"] = lancamentos.select_related(
                'categoria', 'pessoa', 'forma_pagamento',
            ).order_by("-data", "-criado_em")[:5]
        else:
            context["total_lancamentos"] = 0
            context["total_categorias"] = 0
            context["total_pessoas"] = 0
            context["total_formas"] = 0
            context["ultimos_lancamentos"] = []

        return context