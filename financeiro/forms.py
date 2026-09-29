from decimal import Decimal

from django import forms
from django.db.models import Q

from .models import ZERO, Categoria, Centro, FormaPagamento, Lancamento, Parcela, Pessoa


def _opcoes_ativas(modelo, usuario, atual_id=None):
    base = modelo.objects.filter(criado_por=usuario)
    if atual_id:
        return base.filter(Q(status=True) | Q(pk=atual_id)).order_by('nome')
    return base.filter(status=True).order_by('nome')


class AjusteMonetarioMixin:
    def clean_desconto(self):
        return self.cleaned_data.get('desconto') or ZERO

    def clean_acrescimo(self):
        return self.cleaned_data.get('acrescimo') or ZERO


class LancamentoForm(AjusteMonetarioMixin, forms.ModelForm):
    class Meta:
        model = Lancamento
        fields = [
            'tipo', 'data', 'numero', 'categoria', 'centro', 'pessoa', 'forma_pagamento', 'descricao',
            'valor', 'desconto', 'acrescimo', 'parcelas', 'intervalo_parcelas',
            'declara_ir', 'agrupado',
        ]
        # rótulos curtos (não quebram a linha na grade); os textos de ajuda vêm dos modelos
        labels = {
            'data': '1º vencimento',
            'centro': 'Centro de lançamento',
            'pessoa': 'Cliente/Fornecedor',
            'intervalo_parcelas': 'Intervalo (dias)',
            'declara_ir': 'Declara no imposto de renda',
            'agrupado': 'Lançamento agrupado',
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if 'data' in self.fields:
            self.fields['data'].widget = forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')
            self.fields['data'].input_formats = ['%Y-%m-%d']
        if 'parcelas' in self.fields:
            self.fields['parcelas'].initial = 1
            self.fields['parcelas'].widget.attrs['min'] = 1
            self.fields['intervalo_parcelas'].widget.attrs['min'] = 1
            self.fields['valor'].widget.attrs.update({'step': '0.01', 'min': '0.01'})
            self.fields['desconto'].widget.attrs.update({'step': '0.01', 'min': '0'})
            self.fields['acrescimo'].widget.attrs.update({'step': '0.01', 'min': '0'})
            self.fields['desconto'].required = False
            self.fields['acrescimo'].required = False

        if user is not None:
            atual = self.instance
            self.fields['categoria'].queryset = _opcoes_ativas(
                Categoria, user, atual.categoria_id if atual.pk else None,
            )
            self.fields['centro'].queryset = _opcoes_ativas(
                Centro, user, atual.centro_id if atual.pk else None,
            )
            self.fields['pessoa'].queryset = _opcoes_ativas(
                Pessoa, user, atual.pessoa_id if atual.pk else None,
            )
            self.fields['forma_pagamento'].queryset = _opcoes_ativas(
                FormaPagamento, user, atual.forma_pagamento_id if atual.pk else None,
            )

    def clean(self):
        cleaned = super().clean()
        if self.user is not None and not self.instance.criado_por_id:
            self.instance.criado_por = self.user
        return cleaned


class LancamentoUpdateForm(LancamentoForm):
    """Edição cadastral. Valor, quantidade e vencimentos ficam nas parcelas já geradas."""

    class Meta(LancamentoForm.Meta):
        fields = [
            'numero', 'descricao', 'tipo', 'categoria', 'centro', 'pessoa', 'forma_pagamento',
            'declara_ir', 'agrupado',
        ]


class PessoaForm(forms.ModelForm):
    class Meta:
        model = Pessoa
        fields = ['nome', 'documento', 'cep', 'endereco', 'cidade', 'status']

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None and not self.instance.criado_por_id:
            self.instance.criado_por = user


class ParcelaForm(AjusteMonetarioMixin, forms.ModelForm):
    class Meta:
        model = Parcela
        fields = [
            'data', 'forma_pagamento', 'valor', 'desconto', 'acrescimo',
            'valor_pago', 'data_pagamento',
        ]

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        for campo in ('data', 'data_pagamento'):
            self.fields[campo].widget = forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')
            self.fields[campo].input_formats = ['%Y-%m-%d']
        for campo in ('valor', 'desconto', 'acrescimo', 'valor_pago'):
            self.fields[campo].widget.attrs.update({'step': '0.01', 'min': '0'})
        self.fields['desconto'].required = False
        self.fields['acrescimo'].required = False
        self.fields['valor_pago'].required = False
        self.fields['data_pagamento'].required = False

        if user is not None:
            atual = self.instance.forma_pagamento_id if self.instance.pk else None
            self.fields['forma_pagamento'].queryset = _opcoes_ativas(FormaPagamento, user, atual)

    def clean_valor_pago(self):
        valor = self.cleaned_data.get('valor_pago')
        if valor == Decimal('0') or valor == ZERO:
            return None
        return valor
