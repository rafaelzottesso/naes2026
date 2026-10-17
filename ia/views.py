import hmac
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Q, Sum
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView, TemplateView, UpdateView
from django_filters.views import FilterView

from .chamada import testar_conexao
from .cota import CotaExcedida, dono_da_cota, mes_atual, situacao_da_cota
from .filters import RequisicaoIAFilter
from .forms import ConfiguracaoIAForm, ConfiguracaoIAUsuarioForm
from .limpeza import apagar_requisicoes_antigas
from .models import ConfiguracaoIA, ConfiguracaoIAUsuario, ConsumoIA, RequisicaoIA
from .provedores import modo_de_acesso
from .provedores.base import ErroConfiguracao, ErroIA


class SomenteSuperusuarioMixin(UserPassesTestMixin):
    """Telas de administração da IA: visitante vai ao login, usuário comum recebe 403."""
    login_url = reverse_lazy('login')

    def test_func(self):
        return self.request.user.is_superuser


def _top_referencias(do_mes):
    grupos = (
        do_mes.exclude(referencia_tipo=None).order_by()
        .values('referencia_tipo', 'referencia_id')
        .annotate(tokens=Sum('tokens_total'), custo=Sum('custo_estimado'))
        .order_by('-tokens')[:5]
    )
    linhas = []
    for grupo in grupos:
        tipo = ContentType.objects.get_for_id(grupo['referencia_tipo'])
        try:
            nome = str(tipo.get_object_for_this_type(pk=grupo['referencia_id']))
        except ObjectDoesNotExist:
            nome = 'Registro removido'
        linhas.append({'nome': nome, 'tokens': grupo['tokens'], 'custo': grupo['custo']})
    return linhas


def _top_usuarios(do_mes):
    grupos = (
        do_mes.order_by().values('usuario__username')
        .annotate(tokens=Sum('tokens_total'), custo=Sum('custo_estimado'))
        .order_by('-tokens')[:5]
    )
    return [
        {'nome': grupo['usuario__username'], 'tokens': grupo['tokens'], 'custo': grupo['custo']}
        for grupo in grupos
    ]


def _resumo_do_mes():
    """Resumo do mês corrente, sempre sem os filtros da lista."""
    mes = mes_atual()
    hoje = timezone.localdate()
    do_mes = RequisicaoIA.objects.filter(criado_em__date__gte=mes)
    totais = do_mes.aggregate(
        tokens=Sum('tokens_total'),
        custo=Sum('custo_estimado'),
        erros=Count('pk', filter=~Q(situacao='sucesso')),
    )
    periodo = f'periodo_after={mes:%Y-%m-%d}&periodo_before={hoje:%Y-%m-%d}'
    url_lista = reverse('ia:requisicao-list')
    return {
        'mes': mes,
        'resumo': {
            'tokens': totais['tokens'] or 0,
            'custo': totais['custo'] or Decimal('0'),
            'erros': totais['erros'] or 0,
        },
        'url_tokens': f'{url_lista}?{periodo}',
        'url_erros': f'{url_lista}?{periodo}&resultado=erro',
        'top_referencias': _top_referencias(do_mes),
        'top_usuarios': _top_usuarios(do_mes),
    }


class RequisicaoIAList(SomenteSuperusuarioMixin, FilterView):
    model = RequisicaoIA
    filterset_class = RequisicaoIAFilter
    template_name = 'ia/requisicao_list.html'
    paginate_by = 30
    ordering = ['-criado_em']

    def get_queryset(self):
        return super().get_queryset().select_related('usuario', 'referencia_tipo').prefetch_related('referencia')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_resumo_do_mes())
        return context


class RequisicaoIADetail(SomenteSuperusuarioMixin, DetailView):
    model = RequisicaoIA
    template_name = 'ia/requisicao_detail.html'
    context_object_name = 'requisicao'

    def get_queryset(self):
        return super().get_queryset().select_related('usuario', 'referencia_tipo')


class MeuConsumo(LoginRequiredMixin, TemplateView):
    login_url = reverse_lazy('login')
    template_name = 'ia/meu_consumo.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario = self.request.user
        situacao = situacao_da_cota(dono_da_cota(usuario))
        if situacao.esgotada:
            classe_barra = 'bg-danger'
        elif situacao.em_alerta:
            classe_barra = 'bg-warning'
        else:
            classe_barra = 'bg-info'
        context.update({
            'situacao': situacao,
            'classe_barra': classe_barra,
            # Sem custo em dinheiro: o usuário só enxerga os tokens da própria cota.
            'requisicoes': RequisicaoIA.objects.filter(usuario=usuario).order_by('-criado_em')[:20],
        })
        return context


def _descrever_modo_de_acesso(config):
    if config.provedor != 'gemini':
        return 'Não se aplica ao provedor falso (testes).'
    try:
        acesso = modo_de_acesso()
    except ErroConfiguracao as erro:
        return f'Configuração incompleta: {erro}'
    if acesso.modo == 'enterprise':
        return f'Enterprise (Vertex AI) · projeto {acesso.projeto} · região {acesso.regiao}'
    return 'API Key (AI Studio)'


class ConfiguracaoIAUpdate(SomenteSuperusuarioMixin, UpdateView):
    model = ConfiguracaoIA
    form_class = ConfiguracaoIAForm
    template_name = 'ia/configuracao_form.html'
    success_url = reverse_lazy('ia:configuracao')

    def get_object(self, queryset=None):
        return ConfiguracaoIA.objects.get_or_create(pk=1)[0]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['modo_acesso'] = _descrever_modo_de_acesso(self.object)
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Configuração salva. As mudanças valem na próxima chamada, sem deploy.')
        return super().form_valid(form)


class TestarConexao(SomenteSuperusuarioMixin, View):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        try:
            mensagem = testar_conexao(request.user)
        except (ErroIA, CotaExcedida) as erro:
            messages.error(request, f'Falha no teste de conexão: {erro}')
        else:
            messages.success(request, mensagem)
        return redirect('ia:configuracao')


class UsuarioIAList(SomenteSuperusuarioMixin, ListView):
    template_name = 'ia/usuario_list.html'
    paginate_by = 30

    def get_queryset(self):
        return get_user_model().objects.order_by('username')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        padrao = ConfiguracaoIA.obter().limite_mensal_usuario
        mes = mes_atual()
        usuarios = list(context['object_list'])
        consumos = dict(
            ConsumoIA.objects.filter(mes=mes, dono_id__in=[u.pk for u in usuarios])
            .values_list('dono_id', 'tokens_total')
        )
        excecoes = {
            cfg.usuario_id: cfg
            for cfg in ConfiguracaoIAUsuario.objects.filter(usuario_id__in=[u.pk for u in usuarios])
        }
        linhas = []
        for usuario in usuarios:
            cfg = excecoes.get(usuario.pk)
            if cfg is not None and cfg.limite_mensal is not None:
                limite, origem = cfg.limite_mensal, 'próprio'
            else:
                limite, origem = padrao, 'padrão'
            linhas.append({
                'usuario': usuario,
                'limite': limite,
                'origem': origem,
                'uso': consumos.get(usuario.pk, 0),
                'ia_habilitada': cfg.ia_habilitada if cfg is not None else True,
                'tem_excecao': cfg is not None,
            })
        context['linhas'] = linhas
        context['mes'] = mes
        return context


@csrf_exempt
@require_POST
def manutencao(request):
    segredo = settings.TAREFAS_SEGREDO
    enviado = request.headers.get('X-Tarefas-Segredo', '')
    if not segredo or not hmac.compare_digest(enviado.encode(), segredo.encode()):
        return HttpResponseForbidden('Segredo inválido.')
    return JsonResponse({'apagadas': apagar_requisicoes_antigas()})


class UsuarioIAUpdate(SomenteSuperusuarioMixin, UpdateView):
    model = ConfiguracaoIAUsuario
    form_class = ConfiguracaoIAUsuarioForm
    template_name = 'financeiro/form.html'
    success_url = reverse_lazy('ia:usuario-list')

    def get_object(self, queryset=None):
        self.alvo = get_object_or_404(get_user_model(), pk=self.kwargs['usuario_id'])
        return ConfiguracaoIAUsuario.objects.filter(usuario=self.alvo).first() or ConfiguracaoIAUsuario(usuario=self.alvo)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'titulo': f'IA de {self.alvo.username}',
            'botao': 'Atualizar',
            'aviso': 'Deixe o limite vazio para usar o padrão do sistema. Zero bloqueia o uso da IA.',
        })
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Configuração de IA do usuário salva.')
        return super().form_valid(form)


class UsuarioIAVoltarPadrao(SomenteSuperusuarioMixin, View):
    http_method_names = ['post']

    def post(self, request, usuario_id, *args, **kwargs):
        apagados, _ = ConfiguracaoIAUsuario.objects.filter(usuario_id=usuario_id).delete()
        if apagados:
            messages.success(request, 'Usuário voltou ao padrão do sistema.')
        else:
            messages.info(request, 'Este usuário já usa o padrão do sistema.')
        return redirect('ia:usuario-list')
