from django.contrib import admin

from .models import Categoria, Lancamento, Parcela


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'status', 'criado_por')
    list_filter = ('status',)
    search_fields = ('nome',)


@admin.register(Lancamento)
class LancamentoAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'tipo', 'data', 'valor', 'parcelas', 'status', 'criado_por')
    list_filter = ('tipo', 'status')
    search_fields = ('descricao',)


@admin.register(Parcela)
class ParcelaAdmin(admin.ModelAdmin):
    list_display = ('lancamento', 'numero', 'data', 'valor', 'valor_pago', 'data_pagamento')
    list_filter = ('status',)
