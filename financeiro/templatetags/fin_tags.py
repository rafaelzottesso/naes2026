import decimal

from decimal import Decimal

from django import template

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
