import json
from calendar import monthrange
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import DecimalField, ExpressionWrapper, F, Sum, Value
from django.db.models.deletion import ProtectedError
from django.db.models.functions import Coalesce
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, TemplateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
from django_filters.views import FilterView

from .filters import CategoriaFilter, FormaPagamentoFilter, LancamentoFilter, PessoaFilter
from .forms import LancamentoForm, LancamentoUpdateForm, ParcelaForm
from .models import Categoria, FormaPagamento, Lancamento, Parcela, Pessoa
from .services import gerar_parcelas


class BaseLoginMixin(LoginRequiredMixin):
    login_url = reverse_lazy('login')


class RegistroDoUsuarioMixin(BaseLoginMixin):
    """Cada pessoa só acessa os cadastros que ela mesma criou."""

    def get_queryset(self):
        return super().get_queryset().filter(criado_por=self.request.user)


class ProtegidoDeleteMixin:
    mensagem_protegido = 'Este registro está em uso e não pode ser excluído.'
    mensagem_sucesso = 'Registro excluído.'

    def form_valid(self, form):
        self.object = self.get_object()
        try:
            self.object.delete()
        except ProtectedError:
            messages.error(self.request, self.mensagem_protegido)
            return HttpResponseRedirect(self.get_success_url())
        messages.success(self.request, self.mensagem_sucesso)
        return HttpResponseRedirect(self.get_success_url())


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
        'botao': 'Criar categoria',
    }

    def form_valid(self, form):
        form.instance.criado_por = self.request.user
        messages.success(self.request, 'Categoria cadastrada.')
        return super().form_valid(form)


class CategoriaUpdate(RegistroDoUsuarioMixin, UpdateView):
    model = Categoria
    fields = ['nome', 'descricao', 'status']
    template_name = 'financeiro/form.html'
    success_url = reverse_lazy('categoria-list')
    extra_context = {
        'titulo': 'Editar Categoria',
        'botao': 'Atualizar categoria',
    }

    def form_valid(self, form):
        messages.success(self.request, 'Categoria atualizada.')
        return super().form_valid(form)


class CategoriaDelete(ProtegidoDeleteMixin, RegistroDoUsuarioMixin, DeleteView):
    model = Categoria
    template_name = 'financeiro/form.html'
    success_url = reverse_lazy('categoria-list')
    mensagem_protegido = (
        'Esta categoria está em lançamentos e não pode ser excluída. '
        'Inative-a se não quiser mais usá-la.'
    )
    mensagem_sucesso = 'Categoria excluída.'
    extra_context = {
        'titulo': 'Excluir Categoria',
        'botao': 'Sim, excluir!',
    }


class CategoriaList(RegistroDoUsuarioMixin, FilterView):
    model = Categoria
    template_name = 'financeiro/list/categoria.html'
    paginate_by = 30
    ordering = ['nome']
    filterset_class = CategoriaFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        minhas = Categoria.objects.filter(criado_por=self.request.user)
        context['total_categorias'] = minhas.count()
        context['total_ativas'] = minhas.filter(status=True).count()
        return context


class CategoriaDetail(RegistroDoUsuarioMixin, DetailView):
    model = Categoria
    template_name = 'financeiro/detail/categoria.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lancamentos'] = self.object.lancamentos.filter(
            criado_por=self.request.user,
        ).select_related('pessoa', 'forma_pagamento')[:8]
        return context


class PessoaCreate(BaseLoginMixin, CreateView):
    model = Pessoa
    fields = ['nome', 'documento', 'cep', 'endereco', 'cidade', 'status']
    template_name = 'financeiro/form.html'
    success_url = reverse_lazy('pessoa-list')
    extra_context = {
        'titulo': 'Cadastro de Pessoa',
        'botao': 'Criar pessoa',
    }

    def form_valid(self, form):
        form.instance.criado_por = self.request.user
        messages.success(self.request, 'Pessoa cadastrada.')
        return super().form_valid(form)


class PessoaUpdate(RegistroDoUsuarioMixin, UpdateView):
    model = Pessoa
    fields = ['nome', 'documento', 'cep', 'endereco', 'cidade', 'status']
    template_name = 'financeiro/form.html'
    success_url = reverse_lazy('pessoa-list')
    extra_context = {
        'titulo': 'Editar Pessoa',
        'botao': 'Atualizar pessoa',
    }

    def form_valid(self, form):
        messages.success(self.request, 'Pessoa atualizada.')
        return super().form_valid(form)


class PessoaDelete(ProtegidoDeleteMixin, RegistroDoUsuarioMixin, DeleteView):
    model = Pessoa
    template_name = 'financeiro/form.html'
    success_url = reverse_lazy('pessoa-list')
    mensagem_protegido = 'Esta pessoa está vinculada a lançamentos e não pode ser excluída.'
    mensagem_sucesso = 'Pessoa excluída.'
    extra_context = {
        'titulo': 'Excluir Pessoa',
        'botao': 'Sim, excluir!',
    }


class PessoaList(RegistroDoUsuarioMixin, FilterView):
    model = Pessoa
    template_name = 'financeiro/list/pessoa.html'
    paginate_by = 30
    ordering = ['nome']
    filterset_class = PessoaFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        minhas = Pessoa.objects.filter(criado_por=self.request.user)
        context['total_pessoas'] = minhas.count()
        context['total_ativas'] = minhas.filter(status=True).count()
        return context


class PessoaDetail(RegistroDoUsuarioMixin, DetailView):
    model = Pessoa
    template_name = 'financeiro/detail/pessoa.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lancamentos'] = self.object.lancamentos.filter(
            criado_por=self.request.user,
        ).select_related('categoria', 'forma_pagamento')[:8]
        return context


class FormaPagamentoCreate(BaseLoginMixin, CreateView):
    model = FormaPagamento
    fields = ['nome', 'descricao', 'status']
    template_name = 'financeiro/form.html'
    success_url = reverse_lazy('forma-pagamento-list')
    extra_context = {
        'titulo': 'Cadastro de Forma de Pagamento',
        'botao': 'Criar forma de pagamento',
    }

    def form_valid(self, form):
        form.instance.criado_por = self.request.user
        messages.success(self.request, 'Forma de pagamento cadastrada.')
        return super().form_valid(form)


class FormaPagamentoUpdate(RegistroDoUsuarioMixin, UpdateView):
    model = FormaPagamento
    fields = ['nome', 'descricao', 'status']
    template_name = 'financeiro/form.html'
    success_url = reverse_lazy('forma-pagamento-list')
    extra_context = {
        'titulo': 'Editar Forma de Pagamento',
        'botao': 'Atualizar forma de pagamento',
    }

    def form_valid(self, form):
        messages.success(self.request, 'Forma de pagamento atualizada.')
        return super().form_valid(form)


class FormaPagamentoDelete(ProtegidoDeleteMixin, RegistroDoUsuarioMixin, DeleteView):
    model = FormaPagamento
    template_name = 'financeiro/form.html'
    success_url = reverse_lazy('forma-pagamento-list')
    mensagem_protegido = (
        'Esta forma de pagamento está em lançamentos ou parcelas e não pode ser excluída.'
    )
    mensagem_sucesso = 'Forma de pagamento excluída.'
    extra_context = {
        'titulo': 'Excluir Forma de Pagamento',
        'botao': 'Sim, excluir!',
    }


class FormaPagamentoList(RegistroDoUsuarioMixin, FilterView):
    model = FormaPagamento
    template_name = 'financeiro/list/forma_pagamento.html'
    paginate_by = 30
    ordering = ['nome']
    filterset_class = FormaPagamentoFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        minhas = FormaPagamento.objects.filter(criado_por=self.request.user)
        context['total_formas'] = minhas.count()
        context['total_ativas'] = minhas.filter(status=True).count()
        return context


class FormaPagamentoDetail(RegistroDoUsuarioMixin, DetailView):
    model = FormaPagamento
    template_name = 'financeiro/detail/forma_pagamento.html'


class LancamentoCreate(BaseLoginMixin, CreateView):
    model = Lancamento
    form_class = LancamentoForm
    template_name = 'financeiro/form.html'
    extra_context = {
        'titulo': 'Cadastro de Lançamento',
        'botao': 'Criar lançamento',
        'aviso': 'Ao salvar, as parcelas são geradas na hora. À vista conta como 1 parcela.',
    }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not FormaPagamento.objects.filter(criado_por=self.request.user, status=True).exists():
            context['aviso'] = (
                'Cadastre uma forma de pagamento ativa antes de lançar. '
                'À vista conta como 1 parcela.'
            )
        return context

    def get_success_url(self):
        return reverse_lazy('lancamento-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
            gerar_parcelas(self.object)
        messages.success(
            self.request,
            f'Lançamento cadastrado com {self.object.parcelas} parcela(s).',
        )
        return HttpResponseRedirect(self.get_success_url())


class LancamentoUpdate(RegistroDoUsuarioMixin, UpdateView):
    model = Lancamento
    form_class = LancamentoUpdateForm
    template_name = 'financeiro/form.html'
    extra_context = {
        'titulo': 'Editar Lançamento',
        'botao': 'Atualizar lançamento',
        'aviso': (
            'Valor, quantidade e vencimentos não mudam aqui, para não apagar o histórico '
            'das parcelas. Ajuste cada parcela na tela dela. A forma de pagamento do '
            'lançamento não reescreve as parcelas já criadas.'
        ),
    }

    def get_queryset(self):
        return super().get_queryset().select_related('categoria', 'pessoa', 'forma_pagamento')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse_lazy('lancamento-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Lançamento atualizado.')
        return super().form_valid(form)


class LancamentoDelete(ProtegidoDeleteMixin, RegistroDoUsuarioMixin, DeleteView):
    model = Lancamento
    template_name = 'financeiro/form.html'
    success_url = reverse_lazy('lancamento-list')
    mensagem_sucesso = 'Lançamento excluído junto com as parcelas.'
    extra_context = {
        'titulo': 'Excluir Lançamento',
        'botao': 'Sim, excluir!',
    }


class LancamentoList(RegistroDoUsuarioMixin, FilterView):
    model = Lancamento
    template_name = 'financeiro/list/lancamento.html'
    paginate_by = 30
    ordering = ['-data', '-criado_em']
    filterset_class = LancamentoFilter

    def get_queryset(self):
        return super().get_queryset().select_related('categoria', 'pessoa', 'forma_pagamento')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ativos = self.get_queryset().filter(status=True)
        context['total_receitas'] = _soma_liquida(ativos.filter(tipo='receita'))
        context['total_despesas'] = _soma_liquida(ativos.filter(tipo='despesa'))
        context['saldo'] = context['total_receitas'] - context['total_despesas']
        return context


class LancamentoDetail(RegistroDoUsuarioMixin, DetailView):
    model = Lancamento
    template_name = 'financeiro/detail/lancamento.html'

    def get_queryset(self):
        return super().get_queryset().select_related('categoria', 'pessoa', 'forma_pagamento')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['parcelas'] = self.object.itens.select_related('forma_pagamento')
        context['hoje'] = timezone.localdate()
        return context


class ParcelaDoUsuarioMixin(BaseLoginMixin):
    def get_queryset(self):
        return super().get_queryset().filter(
            lancamento__criado_por=self.request.user,
        ).select_related('lancamento', 'lancamento__categoria', 'forma_pagamento')


class ParcelaUpdate(ParcelaDoUsuarioMixin, UpdateView):
    model = Parcela
    form_class = ParcelaForm
    template_name = 'financeiro/form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar parcela {self.object.numero}'
        context['botao'] = 'Salvar parcela'
        context['aviso'] = (
            'Parcela não tem exclusão. Para removê-la, exclua o lançamento, '
            'o que também apaga as outras parcelas.'
        )
        return context

    def get_success_url(self):
        return reverse_lazy('lancamento-detail', kwargs={'pk': self.object.lancamento_id})

    def form_valid(self, form):
        messages.success(self.request, f'Parcela {self.object.numero} atualizada.')
        return super().form_valid(form)


class ParcelaDetail(ParcelaDoUsuarioMixin, DetailView):
    model = Parcela
    template_name = 'financeiro/detail/parcela.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hoje'] = timezone.localdate()
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

        parc = Parcela.objects.filter(
            lancamento__criado_por=user,
            lancamento__status=True,
            status=True,
        ).select_related('lancamento', 'lancamento__categoria', 'forma_pagamento')

        parc_mes = parc.filter(data__range=(inicio_mes, fim_mes))
        receitas_mes = _soma_liquida(parc_mes.filter(lancamento__tipo='receita'))
        despesas_mes = _soma_liquida(parc_mes.filter(lancamento__tipo='despesa'))
        saldo_mes = receitas_mes - despesas_mes

        zero = Value(Decimal('0.00'), output_field=DecimalField(max_digits=12, decimal_places=2))
        pagas_mes = parc.filter(
            lancamento__tipo='despesa',
            data_pagamento__isnull=False,
            data_pagamento__range=(inicio_mes, fim_mes),
        ).aggregate(s=Coalesce(Sum('valor_pago'), zero))['s']

        pendentes = parc.filter(data_pagamento__isnull=True)
        atrasadas = pendentes.filter(data__lt=hoje)
        contas_vencidas = atrasadas.filter(lancamento__tipo='despesa')
        a_pagar = _soma_liquida(pendentes.filter(lancamento__tipo='despesa'))
        a_receber = _soma_liquida(pendentes.filter(lancamento__tipo='receita'))
        atrasado = _soma_liquida(contas_vencidas)

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
        for data_mes in reversed(meses):
            inicio = data_mes
            fim = data_mes.replace(day=monthrange(data_mes.year, data_mes.month)[1])
            receitas = _soma_liquida(parc.filter(lancamento__tipo='receita', data__range=(inicio, fim)))
            despesas = _soma_liquida(parc.filter(lancamento__tipo='despesa', data__range=(inicio, fim)))
            fluxo_labels.append(f'{MESES[data_mes.month - 1]}/{data_mes.year}')
            fluxo_receitas.append(float(receitas))
            fluxo_despesas.append(float(despesas))
            fluxo_saldo.append(float(receitas - despesas))

        cat_qs = (
            parc.filter(lancamento__tipo='despesa')
            .values('lancamento__categoria__nome')
            .annotate(total=Sum('valor'))
            .order_by('-total')[:6]
        )
        cat_labels = [item['lancamento__categoria__nome'] or 'Sem categoria' for item in cat_qs]
        cat_valores = [float(item['total']) for item in cat_qs]

        n_pagas = parc.filter(data_pagamento__isnull=False).count()
        n_pendentes = pendentes.filter(data__gte=hoje).count()
        n_vencidas = atrasadas.count()
        n_contas_vencidas = contas_vencidas.count()

        ctx.update({
            'hoje': hoje,
            'mes_label': f'{MESES_EXT[hoje.month - 1]}/{hoje.year}',
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
            'proximos': pendentes.order_by('data')[:5],
            'ultimos': (
                Lancamento.objects.filter(criado_por=user)
                .select_related('categoria', 'pessoa')
                .order_by('-criado_em')[:5]
            ),
        })
        return ctx
