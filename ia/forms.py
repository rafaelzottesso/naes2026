from django import forms

from .models import ConfiguracaoIA, ConfiguracaoIAUsuario


GRUPOS_CONFIGURACAO = [
    ('Modelo', [
        'provedor', 'modelo', 'temperatura', 'max_tokens_saida', 'nivel_raciocinio', 'tentativas', 'timeout_s',
    ]),
    ('Limites padrão por usuário', [
        'limite_mensal_usuario', 'aviso_percentual', 'reserva_minima_tokens',
    ]),
    ('Proteção do sistema', [
        'limite_mensal_sistema', 'tamanho_maximo_mb', 'pdf_max_paginas', 'reter_requisicoes_dias',
    ]),
    ('Preços (estimativa de custo)', [
        'preco_entrada_milhao', 'preco_saida_milhao',
    ]),
]


class ConfiguracaoIAForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoIA
        fields = [campo for _, campos in GRUPOS_CONFIGURACAO for campo in campos]

    def grupos(self):
        """Campos agrupados por seção, para o template montar um bloco por grupo."""
        return [(titulo, [self[nome] for nome in campos]) for titulo, campos in GRUPOS_CONFIGURACAO]


class ConfiguracaoIAUsuarioForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoIAUsuario
        fields = ['ia_habilitada', 'limite_mensal', 'observacao']
        widgets = {
            'observacao': forms.Textarea(attrs={'rows': 3}),
        }
