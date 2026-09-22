from django.db import models

# Create your models here.
TIPO_LANCAMENTO = [
    ('receita', 'Receita'),
    ('despesa', 'Despesa'),
]

class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    status = models.BooleanField(default=True, verbose_name='Ativo')

    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['nome']

class Lancamento(models.Model):
    tipo = models.CharField(max_length=10, choices=TIPO_LANCAMENTO, verbose_name='Tipo')
    data = models.DateField(verbose_name='Data')
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor')
    desconto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Desconto', blank=True, null=True)
    acrescimo = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Acrescimo', blank=True, null=True)
    parcelas = models.IntegerField(
        verbose_name='Parcelas',
        blank=True,
        null=True,
        help_text='Deixe vazio para um lançamento à vista (1 parcela).',
    )
    intervalo_parcelas = models.IntegerField(
        verbose_name='Intervalo entre parcelas',
        blank=True,
        null=True,
        help_text='Quantidade de dias entre os vencimentos. Obrigatório quando houver mais de uma parcela.',
    )
    status = models.BooleanField(default=True, verbose_name='Ativo')
    
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Lançamento'
        verbose_name_plural = 'Lançamentos'
        ordering = ['-data', '-criado_em']

    def __str__(self):
        return f"{self.descricao} - {self.valor}"

    @property
    def valor_total(self):
        desconto = self.desconto or 0
        acrescimo = self.acrescimo or 0
        return self.valor - desconto + acrescimo


class Parcela(models.Model):
    lancamento = models.ForeignKey(Lancamento, on_delete=models.CASCADE)
    numero = models.IntegerField(verbose_name='Número da parcela')
    data = models.DateField(verbose_name='Data')
    
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor')
    desconto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Desconto', blank=True, null=True)
    acrescimo = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Acrescimo', blank=True, null=True)
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor pago', blank=True, null=True)
    data_pagamento = models.DateField(verbose_name='Data de pagamento', blank=True, null=True)
    
    status = models.BooleanField(default=True, verbose_name='Ativo')
    
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Parcela'
        verbose_name_plural = 'Parcelas'
        ordering = ['numero']

    def __str__(self):
        return f"{self.lancamento.descricao} - {self.numero}"