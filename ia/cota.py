from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.db.models import F, Sum

from ia.models import ConfiguracaoIA, ConfiguracaoIAUsuario, ConsumoIA

FUSO = ZoneInfo('America/Sao_Paulo')


class CotaExcedida(Exception):
    def __init__(self, situacao):
        super().__init__(situacao.mensagem_esgotada())
        self.situacao = situacao


@dataclass(frozen=True)
class SituacaoCota:
    usado: int
    limite: int
    restante: int
    percentual: int
    renova_em: date
    esgotada: bool
    em_alerta: bool

    def mensagem_esgotada(self):
        return f'Sua cota de IA acabou. Ela renova em {self.renova_em:%d/%m}.'


def mes_atual():
    return datetime.now(FUSO).date().replace(day=1)


def proximo_mes(mes):
    return (mes + timedelta(days=32)).replace(day=1)


def limite_do_usuario(usuario):
    limite = ConfiguracaoIAUsuario.objects.filter(usuario=usuario).values_list('limite_mensal', flat=True).first()
    if limite is not None:
        return limite
    return ConfiguracaoIA.obter().limite_mensal_usuario


def dono_da_cota(usuario):
    # Hoje o dono é o próprio usuário; com a Conta do plano, esta função passa a devolver a Conta.
    return usuario


def situacao_da_cota(dono):
    config = ConfiguracaoIA.obter()
    mes = mes_atual()
    usado = ConsumoIA.objects.filter(dono=dono, mes=mes).values_list('tokens_total', flat=True).first() or 0
    limite = limite_do_usuario(dono)
    restante = max(limite - usado, 0)
    percentual = min(int(usado * 100 / limite), 100) if limite else 100
    return SituacaoCota(
        usado=usado,
        limite=limite,
        restante=restante,
        percentual=percentual,
        renova_em=proximo_mes(mes),
        esgotada=limite == 0 or restante < config.reserva_minima_tokens,
        em_alerta=percentual >= config.aviso_percentual,
    )


def verificar(dono):
    situacao = situacao_da_cota(dono)
    if situacao.esgotada:
        raise CotaExcedida(situacao)
    return situacao


def teto_do_sistema_atingido():
    limite = ConfiguracaoIA.obter().limite_mensal_sistema
    if not limite:
        return False
    total = ConsumoIA.objects.filter(mes=mes_atual()).aggregate(total=Sum('tokens_total'))['total'] or 0
    return total >= limite


def custo_estimado(uso, config):
    preco_entrada = config.preco_entrada_milhao or Decimal('0')
    preco_saida = config.preco_saida_milhao or Decimal('0')
    total = uso.entrada * preco_entrada + uso.saida * preco_saida
    return (total / Decimal(1_000_000)).quantize(Decimal('0.000001'))


def registrar_consumo(dono, uso, custo):
    mes = mes_atual()
    ConsumoIA.objects.get_or_create(dono=dono, mes=mes)
    ConsumoIA.objects.filter(dono=dono, mes=mes).update(
        tokens_entrada=F('tokens_entrada') + uso.entrada,
        tokens_saida=F('tokens_saida') + uso.saida,
        tokens_total=F('tokens_total') + uso.total,
        custo_estimado=F('custo_estimado') + custo,
        requisicoes=F('requisicoes') + 1,
    )
