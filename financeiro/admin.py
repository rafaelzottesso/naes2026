from django.contrib import admin

from .models import Categoria, Lancamento, Parcela, Pessoa


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'status', 'criado_por')
    list_filter = ('status',)
    search_fields = ('nome',)


@admin.register(Pessoa)
class PessoaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'documento', 'cidade', 'status', 'criado_por')
    list_filter = ('status', 'cidade')
    search_fields = ('nome', 'documento', 'cidade')


@admin.register(Lancamento)
class LancamentoAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'pessoa', 'tipo', 'data', 'valor', 'parcelas', 'status', 'criado_por')
    list_filter = ('tipo', 'status')
    search_fields = ('descricao',)


@admin.register(Parcela)
class ParcelaAdmin(admin.ModelAdmin):
    list_display = ('lancamento', 'numero', 'data', 'valor', 'valor_pago', 'data_pagamento')
    list_filter = ('status',)
