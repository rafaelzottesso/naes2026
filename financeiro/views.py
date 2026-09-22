from decimal import Decimal

from django import forms
from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.db import transaction
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Categoria, Lancamento
from .services import gerar_parcelas, validar_lancamento


class BaseLoginMixin(LoginRequiredMixin):
    login_url = reverse_lazy('login')


def _soma_liquida(queryset):
    zero = Value(Decimal('0.00'), output_field=DecimalField(max_digits=12, decimal_places=2))
    liquido = ExpressionWrapper(
        F('valor') - Coalesce(F('desconto'), zero) + Coalesce(F('acrescimo'), zero),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    total = queryset.aggregate(total=Sum(liquido))['total']
    return total or Decimal('0.00')


class CategoriaCreate(BaseLoginMixin, CreateView):
    model = Categoria
    fields = ['nome', 'descricao', 'status']
    template_name = 'financeiro/form.html'
    success_url = reverse_lazy('categoria-list')
    extra_context = {
        'titulo': 'Cadastro de Categoria',
        'botao': 'Criar Categoria',
    }

    def form_valid(self, form):
        form.instance.criado_por = self.request.user
        return super().form_valid(form)


class CategoriaUpdate(BaseLoginMixin, UpdateView):
    model = Categoria
    fields = ['nome', 'descricao', 'status']
    template_name = 'financeiro/form.html'
    success_url = reverse_lazy('categoria-list')
    extra_context = {
        'titulo': 'Editar Categoria',
        'botao': 'Atualizar Categoria',
    }


class CategoriaDelete(BaseLoginMixin, DeleteView):
    model = Categoria
    template_name = 'financeiro/form.html'
    success_url = reverse_lazy('categoria-list')
    extra_context = {
        'titulo': 'Excluir Categoria',
        'botao': 'Sim, excluir!',
    }


class CategoriaList(BaseLoginMixin, ListView):
    model = Categoria
    template_name = 'financeiro/list/categoria.html'
    paginate_by = 30

    def get_queryset(self):
        return super().get_queryset().order_by('nome')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_categorias'] = self.get_queryset().count()
        context['total_ativas'] = self.get_queryset().filter(status=True).count()
        return context


class CategoriaDetail(BaseLoginMixin, DetailView):
    model = Categoria
    template_name = 'financeiro/detail/categoria.html'


class LancamentoCreate(BaseLoginMixin, CreateView):
    model = Lancamento
    fields = [
        'tipo', 'data', 'categoria', 'descricao', 'valor',
        'desconto', 'acrescimo', 'parcelas', 'intervalo_parcelas', 'status',
    ]
    template_name = 'financeiro/form.html'
    extra_context = {
        'titulo': 'Cadastro de Lançamento',
        'botao': 'Criar Lançamento',
        'largura': 8,
    }

    def get_success_url(self):
        return reverse_lazy('lancamento-detail', kwargs={'pk': self.object.pk})

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['data'].widget = forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')
        form.fields['data'].input_formats = ['%Y-%m-%d']
        form.fields['categoria'].queryset = Categoria.objects.filter(status=True).order_by('nome')
        return form

    def form_valid(self, form):
        form.instance.criado_por = self.request.user
        erros = validar_lancamento(form.instance)
        if erros:
            for campo, mensagem in erros.items():
                form.add_error(campo, mensagem)
            return self.form_invalid(form)

        with transaction.atomic():
            resposta = super().form_valid(form)
            gerar_parcelas(self.object)
            return resposta


class LancamentoUpdate(BaseLoginMixin, UpdateView):
    model = Lancamento
    fields = ['descricao', 'tipo', 'categoria', 'status']
    template_name = 'financeiro/form.html'
    extra_context = {
        'titulo': 'Editar Lançamento',
        'botao': 'Atualizar Lançamento',
    }

    def get_queryset(self):
        return super().get_queryset().filter(criado_por=self.request.user).select_related('categoria')

    def get_success_url(self):
        return reverse_lazy('lancamento-detail', kwargs={'pk': self.object.pk})

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['categoria'].queryset = Categoria.objects.filter(
            Q(status=True) | Q(pk=self.object.categoria_id)
        ).order_by('nome')
        return form

    def form_valid(self, form):
        erros = validar_lancamento(form.instance)
        if erros:
            for campo, mensagem in erros.items():
                form.add_error(campo, mensagem)
            return self.form_invalid(form)
        return super().form_valid(form)


class LancamentoDelete(BaseLoginMixin, DeleteView):
    model = Lancamento
    template_name = 'financeiro/form.html'
    success_url = reverse_lazy('lancamento-list')
    extra_context = {
        'titulo': 'Excluir Lançamento',
        'botao': 'Sim, excluir!',
    }

    def get_queryset(self):
        return super().get_queryset().filter(criado_por=self.request.user)


class LancamentoList(BaseLoginMixin, ListView):
    model = Lancamento
    template_name = 'financeiro/list/lancamento.html'
    paginate_by = 30

    def get_queryset(self):
        return super().get_queryset().filter(
            criado_por=self.request.user
        ).select_related('categoria').order_by('-data', '-criado_em')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ativos = self.get_queryset().filter(status=True)
        context['total_receitas'] = _soma_liquida(ativos.filter(tipo='receita'))
        context['total_despesas'] = _soma_liquida(ativos.filter(tipo='despesa'))
        context['saldo'] = context['total_receitas'] - context['total_despesas']
        return context


class LancamentoDetail(BaseLoginMixin, DetailView):
    model = Lancamento
    template_name = 'financeiro/detail/lancamento.html'

    def get_queryset(self):
        return super().get_queryset().filter(
            criado_por=self.request.user
        ).select_related('categoria')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['parcelas'] = self.object.parcela_set.order_by('numero')
        return context
