import decimal

from decimal import Decimal

from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def brl(valor):
    """Formata um valor como moeda brasileira: R$ 1.234,56 (ou -R$ 1.234,56)."""
    try:
        numero = Decimal(valor)
    except (TypeError, ValueError, decimal.InvalidOperation):
        return valor
    texto = f"{abs(numero):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"-R$ {texto}" if numero < 0 else f"R$ {texto}"


SITUACOES_PARCELA = {
    'paga': ('Paga', 'bi-check-circle-fill', 'success'),
    'atrasada': ('Vencida', 'bi-exclamation-octagon-fill', 'danger'),
    'vence_hoje': ('Vence hoje', 'bi-alarm-fill', 'warning'),
    'a_vencer': ('Em aberto', 'bi-hourglass-split', 'info'),
}


def _plural_dias(dias):
    return f'{dias} dia' if dias == 1 else f'{dias} dias'


@register.inclusion_tag('financeiro/_situacao.html')
def situacao_parcela(parcela, com_detalhe=False):
    """Selo padrão da parcela: paga (verde-água), vencida (salmão), vence hoje (âmbar), em aberto (azul)."""
    hoje = timezone.localdate()
    chave = parcela.situacao
    detalhe = ''
    if chave == 'paga':
        detalhe = f'em {parcela.data_pagamento:%d/%m/%Y}'
    elif chave == 'atrasada':
        detalhe = f'há {_plural_dias((hoje - parcela.data).days)}'
    elif parcela.data == hoje:
        chave = 'vence_hoje'
    else:
        detalhe = f'em {_plural_dias((parcela.data - hoje).days)}'
    rotulo, icone, cor = SITUACOES_PARCELA[chave]
    return {'chave': chave, 'rotulo': rotulo, 'icone': icone, 'cor': cor, 'detalhe': detalhe if com_detalhe else ''}


@register.inclusion_tag('financeiro/_situacao.html')
def situacao_lancamento(lancamento):
    """Selo do lançamento a partir das contagens anotadas na lista (n_parcelas, n_pagas, n_vencidas)."""
    if lancamento.n_vencidas:
        rotulo, icone, cor = 'Parcela vencida', 'bi-exclamation-octagon-fill', 'danger'
    elif lancamento.n_pagas and lancamento.n_pagas == lancamento.n_parcelas:
        rotulo, icone, cor = 'Quitado', 'bi-check-circle-fill', 'success'
    else:
        rotulo, icone, cor = 'Em aberto', 'bi-hourglass-split', 'info'
    detalhe = f'{lancamento.n_pagas}/{lancamento.n_parcelas} pagas'
    return {'chave': cor, 'rotulo': rotulo, 'icone': icone, 'cor': cor, 'detalhe': detalhe}
