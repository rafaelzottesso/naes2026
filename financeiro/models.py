from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


TIPO_LANCAMENTO = [
    ('receita', 'Receita'),
    ('despesa', 'Despesa'),
]

ZERO = Decimal('0.00')
CENTAVO = Decimal('0.01')


class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    status = models.BooleanField(default=True, verbose_name='Ativo')

    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey('auth.User', on_delete=models.PROTECT, related_name='categorias')
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['nome']


class Centro(models.Model):
    """Centro de lançamento: acompanha uma atividade específica (viagem, reforma, projeto)."""

    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    status = models.BooleanField(default=True, verbose_name='Ativo')

    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey('auth.User', on_delete=models.PROTECT, related_name='centros')
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = 'Centro de lançamento'
        verbose_name_plural = 'Centros de lançamento'
        ordering = ['nome']


class Pessoa(models.Model):
    nome = models.CharField(max_length=150, verbose_name='Nome')
    documento = models.CharField(max_length=18, verbose_name='CPF ou CNPJ')
    cep = models.CharField(max_length=9, verbose_name='CEP')
    endereco = models.CharField(max_length=255, verbose_name='Endereço')
    cidade = models.CharField(max_length=100, verbose_name='Cidade')
    status = models.BooleanField(default=True, verbose_name='Ativo')

    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey('auth.User', on_delete=models.PROTECT, related_name='pessoas')
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome

    def clean(self):
        erros = {}
        digitos = ''.join(caractere for caractere in (self.documento or '') if caractere.isdigit())
        if digitos and len(digitos) not in (11, 14):
            erros['documento'] = 'Informe um CPF com 11 dígitos ou um CNPJ com 14 dígitos.'
        cep = ''.join(caractere for caractere in (self.cep or '') if caractere.isdigit())
        if cep and len(cep) != 8:
            erros['cep'] = 'Informe um CEP com 8 dígitos.'
        if self.documento and self.criado_por_id:
            repetidas = Pessoa.objects.filter(criado_por_id=self.criado_por_id, documento=self.documento)
            if self.pk:
                repetidas = repetidas.exclude(pk=self.pk)
            if repetidas.exists():
                erros['documento'] = 'Você já cadastrou uma pessoa com este CPF ou CNPJ.'
        if erros:
            raise ValidationError(erros)

    class Meta:
        verbose_name = 'Pessoa'
        verbose_name_plural = 'Pessoas'
        ordering = ['nome']
        constraints = [
            models.UniqueConstraint(
                fields=['criado_por', 'documento'],
                name='pessoa_documento_unico_por_usuario',
            ),
        ]


class FormaPagamento(models.Model):
    nome = models.CharField(max_length=80, verbose_name='Nome')
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    status = models.BooleanField(default=True, verbose_name='Ativo')

    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey('auth.User', on_delete=models.PROTECT, related_name='formas_pagamento')
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = 'Forma de pagamento'
        verbose_name_plural = 'Formas de pagamento'
        ordering = ['nome']


class Lancamento(models.Model):
    tipo = models.CharField(max_length=10, choices=TIPO_LANCAMENTO, verbose_name='Tipo')
    data = models.DateField(verbose_name='Data da primeira parcela')
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='lancamentos',
        verbose_name='Categoria',
    )
    centro = models.ForeignKey(
        Centro,
        on_delete=models.PROTECT,
        related_name='lancamentos',
        null=True,
        blank=True,
        verbose_name='Centro de lançamento',
        help_text='Opcional. Use para acompanhar uma viagem, reforma ou projeto.',
    )
    pessoa = models.ForeignKey(
        Pessoa,
        on_delete=models.PROTECT,
        related_name='lancamentos',
        verbose_name='Cliente/Fornecedor',
    )
    forma_pagamento = models.ForeignKey(
        FormaPagamento,
        on_delete=models.PROTECT,
        related_name='lancamentos',
        null=True,
        blank=False,
        verbose_name='Forma de pagamento',
        help_text='As parcelas nascem com esta forma. Depois, cada parcela pode ser paga de outro jeito.',
    )
    numero = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Número',
        help_text='Número da nota, do boleto ou do documento. Opcional.',
    )
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    declara_ir = models.BooleanField(
        default=False,
        verbose_name='Declara no imposto de renda',
        help_text='Marque se este lançamento deve entrar na declaração do imposto de renda.',
    )
    agrupado = models.BooleanField(
        default=False,
        verbose_name='Lançamento agrupado',
        help_text='Marque se este lançamento junta várias notas em um só.',
    )

    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Valor',
        validators=[MinValueValidator(CENTAVO, 'Informe um valor maior que zero.')],
    )
    desconto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Desconto',
        blank=True,
        null=True,
        default=ZERO,
        validators=[MinValueValidator(ZERO, 'O desconto não pode ser negativo.')],
    )
    acrescimo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Acréscimo',
        blank=True,
        null=True,
        default=ZERO,
        validators=[MinValueValidator(ZERO, 'O acréscimo não pode ser negativo.')],
    )
    parcelas = models.PositiveIntegerField(
        default=1,
        null=True,
        blank=False,
        verbose_name='Parcelas',
        validators=[
            MinValueValidator(1, 'Informe pelo menos 1 parcela. Compras à vista usam 1.'),
            MaxValueValidator(480, 'Use no máximo 480 parcelas.'),
        ],
        help_text='Mínimo de 1. À vista, débito e crédito em uma vez usam 1 parcela.',
    )
    intervalo_parcelas = models.PositiveIntegerField(
        verbose_name='Intervalo entre parcelas (dias)',
        blank=True,
        null=True,
        validators=[MinValueValidator(1, 'O intervalo precisa ser de pelo menos 1 dia.')],
        help_text='Obrigatório quando houver mais de uma parcela. Em dias corridos.',
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey('auth.User', on_delete=models.PROTECT, related_name='lancamentos')
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Lançamento'
        verbose_name_plural = 'Lançamentos'
        ordering = ['-data', '-criado_em']

    def __str__(self):
        if self.descricao:
            rotulo = self.descricao
        elif self.categoria_id:
            rotulo = self.categoria.nome
        else:
            rotulo = 'Lançamento'
        return f'{rotulo} — {self.valor}'

    @property
    def valor_total(self):
        desconto = self.desconto or ZERO
        acrescimo = self.acrescimo or ZERO
        return (self.valor or ZERO) - desconto + acrescimo

    def clean(self):
        erros = {}
        quantidade = self.parcelas or 0

        if not self.forma_pagamento_id:
            erros['forma_pagamento'] = 'Escolha a forma de pagamento.'

        if quantidade < 1:
            erros['parcelas'] = 'Informe pelo menos 1 parcela. Compras à vista usam 1.'
        elif quantidade > 1 and (not self.intervalo_parcelas or self.intervalo_parcelas < 1):
            erros['intervalo_parcelas'] = 'Informe o intervalo em dias quando houver mais de uma parcela.'

        if quantidade == 1:
            self.intervalo_parcelas = None

        if self.valor is not None and self.valor_total <= 0:
            erros['valor'] = 'O valor líquido (valor − desconto + acréscimo) precisa ser maior que zero.'
        elif quantidade >= 1 and self.valor is not None and self.valor_total < CENTAVO * quantidade:
            erros['parcelas'] = (
                'O valor líquido não cobre essa quantidade de parcelas '
                '(mínimo de R$ 0,01 em cada uma).'
            )

        if self.criado_por_id:
            self._validar_dono(erros)

        if erros:
            raise ValidationError(erros)

    def _validar_dono(self, erros):
        if self.categoria_id and self.categoria.criado_por_id != self.criado_por_id:
            erros['categoria'] = 'Escolha uma categoria da sua conta.'
        elif self.categoria_id and not self.categoria.status and not self.pk:
            erros['categoria'] = 'Escolha uma categoria ativa.'

        if self.centro_id and self.centro.criado_por_id != self.criado_por_id:
            erros['centro'] = 'Escolha um centro de lançamento da sua conta.'
        elif self.centro_id and not self.centro.status and not self.pk:
            erros['centro'] = 'Escolha um centro de lançamento ativo.'

        if self.pessoa_id and self.pessoa.criado_por_id != self.criado_por_id:
            erros['pessoa'] = 'Escolha uma pessoa da sua conta.'
        elif self.pessoa_id and not self.pessoa.status and not self.pk:
            erros['pessoa'] = 'Escolha uma pessoa ativa.'

        if self.forma_pagamento_id and self.forma_pagamento.criado_por_id != self.criado_por_id:
            erros['forma_pagamento'] = 'Escolha uma forma de pagamento da sua conta.'
        elif self.forma_pagamento_id and not self.forma_pagamento.status and not self.pk:
            erros['forma_pagamento'] = 'Escolha uma forma de pagamento ativa.'


class Parcela(models.Model):
    lancamento = models.ForeignKey(
        Lancamento,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='Lançamento',
    )
    numero = models.PositiveIntegerField(verbose_name='Número da parcela')
    data = models.DateField(verbose_name='Vencimento')
    forma_pagamento = models.ForeignKey(
        FormaPagamento,
        on_delete=models.PROTECT,
        related_name='parcelas',
        null=True,
        blank=False,
        verbose_name='Forma de pagamento',
        help_text='Na criação fica igual à do lançamento. Altere aqui se esta parcela for paga de outra forma.',
    )

    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Valor',
        validators=[MinValueValidator(CENTAVO, 'Informe um valor maior que zero.')],
    )
    desconto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Desconto',
        blank=True,
        null=True,
        default=ZERO,
        validators=[MinValueValidator(ZERO, 'O desconto não pode ser negativo.')],
    )
    acrescimo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Acréscimo',
        blank=True,
        null=True,
        default=ZERO,
        validators=[MinValueValidator(ZERO, 'O acréscimo não pode ser negativo.')],
    )
    valor_pago = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Valor pago',
        blank=True,
        null=True,
        validators=[MinValueValidator(CENTAVO, 'O valor pago precisa ser maior que zero.')],
    )
    data_pagamento = models.DateField(verbose_name='Data de pagamento', blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey('auth.User', on_delete=models.PROTECT, related_name='parcelas')
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Parcela'
        verbose_name_plural = 'Parcelas'
        ordering = ['numero']
        constraints = [
            models.UniqueConstraint(
                fields=['lancamento', 'numero'],
                name='parcela_unica_por_lancamento',
            ),
        ]

    def __str__(self):
        return f'Parcela {self.numero} — {self.lancamento}'

    @property
    def valor_liquido(self):
        desconto = self.desconto or ZERO
        acrescimo = self.acrescimo or ZERO
        return (self.valor or ZERO) - desconto + acrescimo

    @property
    def quitada(self):
        return self.data_pagamento is not None and self.valor_pago is not None

    @property
    def situacao(self):
        if self.quitada:
            return 'paga'
        if self.data and self.data < timezone.localdate():
            return 'atrasada'
        return 'a_vencer'

    def clean(self):
        erros = {}
        if not self.forma_pagamento_id:
            erros['forma_pagamento'] = 'Escolha a forma de pagamento.'

        if self.valor is not None and self.valor_liquido < 0:
            erros['valor'] = 'O valor líquido da parcela não pode ser negativo.'

        informou_valor = self.valor_pago is not None
        informou_data = self.data_pagamento is not None
        if informou_valor != informou_data:
            mensagem = 'Informe o valor pago e a data de pagamento juntos, ou deixe os dois em branco.'
            erros['valor_pago'] = mensagem
            erros['data_pagamento'] = mensagem

        if self.lancamento_id and self.criado_por_id and self.lancamento.criado_por_id != self.criado_por_id:
            erros['lancamento'] = 'A parcela precisa pertencer a um lançamento seu.'

        if (
            self.forma_pagamento_id
            and self.lancamento_id
            and self.forma_pagamento.criado_por_id != self.lancamento.criado_por_id
        ):
            erros['forma_pagamento'] = 'Escolha uma forma de pagamento da sua conta.'

        if erros:
            raise ValidationError(erros)
