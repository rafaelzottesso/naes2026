from decimal import Decimal

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q


CACHE_CHAVE = 'ia_configuracao'


class ConfiguracaoIA(models.Model):
    PROVEDORES = [
        ('gemini', 'Gemini (Vertex AI)'),
        ('falso', 'Falso (testes)'),
    ]
    NIVEIS_RACIOCINIO = [
        ('', 'Padrão do modelo'),
        ('low', 'Baixo'),
        ('medium', 'Médio'),
        ('high', 'Alto'),
    ]

    provedor = models.CharField(
        'provedor', max_length=20, choices=PROVEDORES, default='gemini',
        help_text='Quem atende os pedidos de IA.',
    )
    modelo = models.CharField(
        'modelo', max_length=100, default='gemini-3.5-flash-lite',
        help_text='Nome do modelo no Vertex AI.',
    )
    temperatura = models.DecimalField(
        'temperatura', max_digits=3, decimal_places=2, default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('2'))],
        help_text='De 0 a 2. Valores baixos deixam a resposta mais previsível.',
    )
    max_tokens_saida = models.PositiveIntegerField(
        'máximo de tokens de saída', default=8192,
        help_text='Limite de tokens da resposta, incluindo o raciocínio.',
    )
    nivel_raciocinio = models.CharField(
        'nível de raciocínio', max_length=10, choices=NIVEIS_RACIOCINIO, default='low', blank=True,
        help_text='Vale a partir do Gemini 3. Para modelos 2.5, deixe em "Padrão do modelo".',
    )
    tentativas = models.PositiveSmallIntegerField(
        'tentativas', default=2,
        help_text='Número total de tentativas em caso de erro temporário.',
    )
    timeout_s = models.PositiveIntegerField(
        'tempo limite (segundos)', default=60,
        help_text='Tempo máximo de espera por uma resposta.',
    )
    limite_mensal_usuario = models.PositiveIntegerField(
        'limite mensal por usuário (tokens)', default=100000,
        help_text='Padrão para os usuários sem limite próprio. Zero bloqueia o uso.',
    )
    aviso_percentual = models.PositiveSmallIntegerField(
        'aviso de consumo (%)', default=80,
        validators=[MaxValueValidator(100)],
        help_text='Percentual do limite a partir do qual o usuário é avisado.',
    )
    reserva_minima_tokens = models.PositiveIntegerField(
        'reserva mínima (tokens)', default=5000,
        help_text='Tokens que precisam sobrar na cota para aceitar um novo pedido.',
    )
    limite_mensal_sistema = models.PositiveIntegerField(
        'limite mensal do sistema (tokens)', default=20000000,
        help_text='Teto de tokens de todos os usuários no mês. Zero desliga o teto.',
    )
    tamanho_maximo_mb = models.PositiveSmallIntegerField(
        'tamanho máximo do arquivo (MB)', default=10,
        help_text='Tamanho máximo de cada arquivo enviado à IA.',
    )
    pdf_max_paginas = models.PositiveSmallIntegerField(
        'máximo de páginas de PDF', default=10,
        help_text='Número máximo de páginas de cada PDF enviado.',
    )
    reter_requisicoes_dias = models.PositiveSmallIntegerField(
        'reter registros de chamadas (dias)', default=60,
        help_text='Prazo para apagar o registro de chamadas antigas.',
    )
    preco_entrada_milhao = models.DecimalField(
        'preço de entrada por milhão de tokens (US$)', max_digits=10, decimal_places=4,
        null=True, blank=True,
        help_text='Opcional. Usado só para estimar custo.',
    )
    preco_saida_milhao = models.DecimalField(
        'preço de saída por milhão de tokens (US$)', max_digits=10, decimal_places=4,
        null=True, blank=True,
        help_text='Opcional. Usado só para estimar custo.',
    )
    atualizado_em = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'configuração de IA'
        verbose_name_plural = 'configuração de IA'
        constraints = [
            models.CheckConstraint(condition=Q(pk=1), name='ia_configuracao_unica'),
        ]

    def __str__(self):
        return f'Configuração de IA ({self.provedor}, {self.modelo})'

    @classmethod
    def obter(cls):
        config = cache.get(CACHE_CHAVE)
        if config is None:
            config, _ = cls.objects.get_or_create(pk=1)
            cache.set(CACHE_CHAVE, config, 30)
        return config

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete(CACHE_CHAVE)


class ConfiguracaoIAUsuario(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='configuracao_ia',
        verbose_name='usuário',
    )
    ia_habilitada = models.BooleanField(
        'IA habilitada', default=True,
        help_text='Desmarque para impedir este usuário de usar a IA.',
    )
    limite_mensal = models.PositiveIntegerField(
        'limite mensal (tokens)', null=True, blank=True,
        help_text='Vazio usa o padrão do sistema. Zero bloqueia o uso.',
    )
    observacao = models.TextField('observação', blank=True)

    class Meta:
        verbose_name = 'configuração de IA do usuário'
        verbose_name_plural = 'configurações de IA dos usuários'

    def __str__(self):
        return f'IA de {self.usuario}'


class RequisicaoIA(models.Model):
    ORIGENS = [
        ('site', 'Site'),
        ('telegram', 'Telegram'),
        ('comando', 'Comando'),
    ]
    SITUACOES = [
        ('sucesso', 'Sucesso'),
        ('resposta_invalida', 'Resposta inválida'),
        ('erro_temporario', 'Erro temporário'),
        ('erro_permanente', 'Erro permanente'),
        ('tempo_esgotado', 'Tempo esgotado'),
        ('bloqueada_cota', 'Bloqueada pela cota'),
        ('bloqueada_seguranca', 'Bloqueada por segurança'),
        ('indisponivel', 'Indisponível'),
        ('erro_configuracao', 'Erro de configuração'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='requisicoes_ia',
        verbose_name='usuário',
    )
    referencia_tipo = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
        verbose_name='tipo da referência',
    )
    referencia_id = models.PositiveBigIntegerField('ID da referência', null=True, blank=True)
    referencia = GenericForeignKey('referencia_tipo', 'referencia_id')
    origem = models.CharField('origem', max_length=20, choices=ORIGENS, default='site')
    finalidade = models.CharField('finalidade', max_length=60, db_index=True)
    provedor = models.CharField('provedor', max_length=20)
    modelo = models.CharField('modelo', max_length=100, blank=True)
    versao_prompt = models.CharField('versão do prompt', max_length=20, blank=True)
    tentativa = models.PositiveSmallIntegerField('tentativa', default=1)
    situacao = models.CharField('situação', max_length=30, choices=SITUACOES)
    tokens_entrada = models.PositiveIntegerField('tokens de entrada', default=0)
    tokens_saida = models.PositiveIntegerField('tokens de saída', default=0)
    tokens_raciocinio = models.PositiveIntegerField('tokens de raciocínio', default=0)
    tokens_total = models.PositiveIntegerField('tokens total', default=0)
    custo_estimado = models.DecimalField(
        'custo estimado (US$)', max_digits=12, decimal_places=6, default=Decimal('0'),
    )
    duracao_ms = models.PositiveIntegerField('duração (ms)', default=0)
    motivo_fim = models.CharField('motivo do fim', max_length=50, blank=True)
    arquivo_mime = models.CharField('tipo do arquivo', max_length=100, blank=True)
    arquivo_tamanho = models.PositiveIntegerField('tamanho do arquivo (bytes)', null=True, blank=True)
    arquivo_hash = models.CharField('hash do arquivo', max_length=64, blank=True)
    resposta = models.TextField('resposta', blank=True, help_text='Cortada em 20 mil caracteres.')
    erro = models.TextField('erro', blank=True)
    contexto_hash = models.CharField(
        'hash do contexto', max_length=64, blank=True,
        help_text='SHA-256 do texto enviado. O texto em si não é guardado.',
    )
    criado_em = models.DateTimeField('criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'requisição de IA'
        verbose_name_plural = 'requisições de IA'
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['usuario', '-criado_em']),
            models.Index(fields=['situacao', '-criado_em']),
            models.Index(fields=['referencia_tipo', 'referencia_id', '-criado_em']),
        ]

    def __str__(self):
        return f'{self.finalidade} ({self.situacao})'


class ConsumoIA(models.Model):
    dono = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='consumos_ia',
        verbose_name='dono da cota',
    )
    mes = models.DateField('mês', db_index=True, help_text='Sempre o dia 1.')
    tokens_entrada = models.PositiveBigIntegerField('tokens de entrada', default=0)
    tokens_saida = models.PositiveBigIntegerField('tokens de saída', default=0)
    tokens_total = models.PositiveBigIntegerField('tokens total', default=0)
    custo_estimado = models.DecimalField(
        'custo estimado (US$)', max_digits=12, decimal_places=6, default=Decimal('0'),
    )
    requisicoes = models.PositiveIntegerField('requisições', default=0)

    class Meta:
        verbose_name = 'consumo de IA'
        verbose_name_plural = 'consumos de IA'
        ordering = ['-mes']
        constraints = [
            models.UniqueConstraint(fields=['dono', 'mes'], name='ia_consumo_dono_mes_unico'),
        ]

    def __str__(self):
        return f'{self.dono} ({self.mes:%m/%Y})'
