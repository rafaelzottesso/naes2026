from datetime import timedelta
from decimal import Decimal, ROUND_DOWN

from django.db import transaction

from .models import Parcela


def validar_lancamento(lancamento):
    """Regras que o formulário genérico não cobre sozinho."""
    erros = {}
    quantidade = lancamento.parcelas or 1

    if lancamento.categoria_id:
        if not lancamento.categoria.status:
            erros['categoria'] = 'Escolha uma categoria ativa.'

    if lancamento.parcelas is not None and lancamento.parcelas < 1:
        erros['parcelas'] = 'Informe pelo menos 1 parcela, ou deixe o campo vazio para à vista.'

    if quantidade > 1 and (not lancamento.intervalo_parcelas or lancamento.intervalo_parcelas < 1):
        erros['intervalo_parcelas'] = 'Informe o intervalo em dias quando houver mais de uma parcela.'

    if lancamento.valor is not None and lancamento.valor_total < 0:
        erros['valor'] = 'O valor líquido (valor − desconto + acréscimo) não pode ser negativo.'

    return erros


def dividir_valor(total, quantidade):
    """Divide o total em parcelas de 2 casas. A última recebe o resto."""
    quantia = (total / quantidade).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
    valores = [quantia] * (quantidade - 1)
    valores.append(total - quantia * (quantidade - 1))
    return valores


def gerar_parcelas(lancamento):
    quantidade = lancamento.parcelas or 1
    intervalo = lancamento.intervalo_parcelas or 0
    if quantidade == 1:
        intervalo = 0

    valores = dividir_valor(lancamento.valor_total, quantidade)

    with transaction.atomic():
        for numero, valor in enumerate(valores, start=1):
            Parcela.objects.create(
                lancamento=lancamento,
                numero=numero,
                data=lancamento.data + timedelta(days=(numero - 1) * intervalo),
                valor=valor,
                status=True,
                criado_por=lancamento.criado_por,
            )
