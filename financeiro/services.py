from datetime import timedelta
from decimal import Decimal, ROUND_DOWN

from django.db import transaction

from .models import CENTAVO, Parcela


def dividir_valor(total, quantidade):
    """Divide o total em parcelas de 2 casas. A última recebe o centavo que sobra."""
    if quantidade < 1:
        raise ValueError('A quantidade de parcelas precisa ser pelo menos 1.')

    total = Decimal(total).quantize(CENTAVO)
    quantia = (total / quantidade).quantize(CENTAVO, rounding=ROUND_DOWN)
    valores = [quantia] * (quantidade - 1)
    valores.append((total - quantia * (quantidade - 1)).quantize(CENTAVO))
    return valores


def gerar_parcelas(lancamento):
    """Cria as parcelas do lançamento uma única vez, copiando a forma de pagamento."""
    if lancamento.itens.exists():
        return []

    quantidade = lancamento.parcelas or 1
    intervalo = lancamento.intervalo_parcelas or 0
    if quantidade == 1:
        intervalo = 0

    valores = dividir_valor(lancamento.valor_total, quantidade)
    criadas = []

    with transaction.atomic():
        for numero, valor in enumerate(valores, start=1):
            criadas.append(Parcela.objects.create(
                lancamento=lancamento,
                numero=numero,
                data=lancamento.data + timedelta(days=(numero - 1) * intervalo),
                valor=valor,
                desconto=Decimal('0.00'),
                acrescimo=Decimal('0.00'),
                forma_pagamento=lancamento.forma_pagamento,
                status=True,
                criado_por=lancamento.criado_por,
            ))

    return criadas
