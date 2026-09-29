from django.contrib import admin

from .models import Categoria, Centro, FormaPagamento, Lancamento, Parcela, Pessoa
from .services import gerar_parcelas


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'status', 'criado_por')
    list_filter = ('status',)
    search_fields = ('nome',)


@admin.register(Centro)
class CentroAdmin(admin.ModelAdmin):
    list_display = ('nome', 'status', 'criado_por')
    list_filter = ('status',)
    search_fields = ('nome',)


@admin.register(Pessoa)
class PessoaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'documento', 'cidade', 'status', 'criado_por')
    list_filter = ('status', 'cidade')
    search_fields = ('nome', 'documento', 'cidade')


@admin.register(FormaPagamento)
class FormaPagamentoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'status', 'criado_por')
    list_filter = ('status',)
    search_fields = ('nome',)


@admin.register(Lancamento)
class LancamentoAdmin(admin.ModelAdmin):
    list_display = (
        'numero', 'descricao', 'pessoa', 'tipo', 'centro', 'data',
        'valor', 'parcelas', 'declara_ir', 'agrupado', 'criado_por',
    )
    list_filter = ('tipo', 'declara_ir', 'agrupado')
    search_fields = ('numero', 'descricao')

    def save_model(self, request, obj, form, change):
        if not obj.criado_por_id:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)
        if not change:
            gerar_parcelas(obj)


@admin.register(Parcela)
class ParcelaAdmin(admin.ModelAdmin):
    list_display = (
        'lancamento', 'numero', 'data', 'forma_pagamento',
        'valor', 'valor_pago', 'data_pagamento',
    )
    
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
