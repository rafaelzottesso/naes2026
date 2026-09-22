import json
from calendar import monthrange
from decimal import Decimal

from django import forms
from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.db import transaction
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, TemplateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Categoria, Lancamento, Parcela
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
        form.fields['categoria'].queryset = Categoria.objects.filter(status=True)
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
        )
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
        ).select_related('categoria')

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
        context['parcelas'] = self.object.parcela_set.all()
        return context


MESES = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
MESES_EXT = [
    'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
    'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
]


class FinanceiroDashboard(BaseLoginMixin, TemplateView):
    """Dashboard na raiz do app financeiro (/financeiro/)."""
    template_name = 'financeiro/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        hoje = timezone.localdate()
        inicio_mes = hoje.replace(day=1)
        fim_mes = hoje.replace(day=monthrange(hoje.year, hoje.month)[1])

        zero = Value(Decimal('0.00'), output_field=DecimalField(max_digits=12, decimal_places=2))

        parc = Parcela.objects.filter(
            lancamento__criado_por=user,
            lancamento__status=True,
            status=True,
        ).select_related('lancamento', 'lancamento__categoria')

        # ----- KPIs do mês corrente (por vencimento da parcela) -----
        parc_mes = parc.filter(data__range=(inicio_mes, fim_mes))
        receitas_mes = parc_mes.filter(lancamento__tipo='receita').aggregate(s=Coalesce(Sum('valor'), zero))['s']
        despesas_mes = parc_mes.filter(lancamento__tipo='despesa').aggregate(s=Coalesce(Sum('valor'), zero))['s']
        saldo_mes = receitas_mes - despesas_mes

        pagas_mes = parc.filter(
            data_pagamento__isnull=False,
            data_pagamento__range=(inicio_mes, fim_mes),
        ).aggregate(s=Coalesce(Sum('valor_pago'), zero))['s']

        pendentes = parc.filter(valor_pago__isnull=True)
        atrasadas = pendentes.filter(data__lt=hoje)
        contas_vencidas = atrasadas.filter(lancamento__tipo='despesa')
        a_pagar = pendentes.filter(lancamento__tipo='despesa').aggregate(s=Coalesce(Sum('valor'), zero))['s']
        a_receber = pendentes.filter(lancamento__tipo='receita').aggregate(s=Coalesce(Sum('valor'), zero))['s']
        atrasado = contas_vencidas.aggregate(s=Coalesce(Sum('valor'), zero))['s']

        # ----- Fluxo dos últimos 6 meses (por vencimento) -----
        meses = []
        cursor = inicio_mes
        for _ in range(6):
            meses.append(cursor)
            cursor = (
                cursor.replace(month=cursor.month - 1)
                if cursor.month > 1
                else cursor.replace(year=cursor.year - 1, month=12)
            )

        fluxo_labels, fluxo_receitas, fluxo_despesas, fluxo_saldo = [], [], [], []
        for d in reversed(meses):
            ini = d
            f = d.replace(day=monthrange(d.year, d.month)[1])
            r = parc.filter(lancamento__tipo='receita', data__range=(ini, f)).aggregate(s=Coalesce(Sum('valor'), zero))['s']
            desp = parc.filter(lancamento__tipo='despesa', data__range=(ini, f)).aggregate(s=Coalesce(Sum('valor'), zero))['s']
            fluxo_labels.append(f"{MESES[d.month - 1]}/{d.year}")
            fluxo_receitas.append(float(r))
            fluxo_despesas.append(float(desp))
            fluxo_saldo.append(float(r - desp))

        # ----- Despesas por categoria (top 6) -----
        cat_qs = (
            parc.filter(lancamento__tipo='despesa')
            .values('lancamento__categoria__nome')
            .annotate(total=Sum('valor'))
            .order_by('-total')[:6]
        )
        cat_labels = [c['lancamento__categoria__nome'] or 'Sem categoria' for c in cat_qs]
        cat_valores = [float(c['total']) for c in cat_qs]

        # ----- Situação das parcelas -----
        n_pagas = parc.filter(valor_pago__isnull=False).count()
        n_pendentes = pendentes.filter(data__gte=hoje).count()
        n_vencidas = atrasadas.count()
        n_contas_vencidas = contas_vencidas.count()

        # ----- Listas -----
        proximos = pendentes.order_by('data')[:5]
        ultimos = Lancamento.objects.filter(criado_por=user).select_related('categoria').order_by('-criado_em')[:5]

        ctx.update({
            'hoje': hoje,
            'mes_label': f"{MESES_EXT[hoje.month - 1]}/{hoje.year}",
            'mes_periodo': f"{inicio_mes.strftime('%d/%m/%Y')} a {fim_mes.strftime('%d/%m/%Y')}",
            'kpi': {
                'saldo': saldo_mes,
                'saldo_positivo': saldo_mes >= 0,
                'receitas': receitas_mes,
                'despesas': despesas_mes,
                'pago': pagas_mes,
                'a_pagar': a_pagar,
                'a_receber': a_receber,
                'atrasado': atrasado,
                'atrasadas_qtd': n_contas_vencidas,
            },
            'graficos': {
                'labels': json.dumps(fluxo_labels, ensure_ascii=False),
                'receitas': json.dumps(fluxo_receitas),
                'despesas': json.dumps(fluxo_despesas),
                'saldo': json.dumps(fluxo_saldo),
                'cat_labels': json.dumps(cat_labels, ensure_ascii=False),
                'cat_valores': json.dumps(cat_valores),
                'status_labels': json.dumps(['Pagas', 'A vencer', 'Atrasadas'], ensure_ascii=False),
                'status_valores': json.dumps([n_pagas, n_pendentes, n_vencidas]),
            },
            'proximos': proximos,
            'ultimos': ultimos,
        })
        return ctx
