from django.contrib import admin

from ia.models import ConfiguracaoIA, ConfiguracaoIAUsuario, ConsumoIA, RequisicaoIA


@admin.register(ConfiguracaoIA)
class ConfiguracaoIAAdmin(admin.ModelAdmin):
    list_display = ('provedor', 'modelo', 'nivel_raciocinio', 'limite_mensal_sistema', 'atualizado_em')

    def has_add_permission(self, request):
        return not ConfiguracaoIA.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ConfiguracaoIAUsuario)
class ConfiguracaoIAUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'ia_habilitada', 'limite_mensal')
    list_filter = ('ia_habilitada',)
    search_fields = ('usuario__username',)
    autocomplete_fields = ('usuario',)


class SomenteLeituraMixin:
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RequisicaoIA)
class RequisicaoIAAdmin(SomenteLeituraMixin, admin.ModelAdmin):
    list_display = ('criado_em', 'usuario', 'finalidade', 'situacao', 'tentativa', 'tokens_total', 'duracao_ms')
    list_filter = ('situacao', 'finalidade', 'origem', 'provedor')
    search_fields = ('usuario__username', 'finalidade')
    date_hierarchy = 'criado_em'
    list_select_related = ('usuario',)
    readonly_fields = [campo.name for campo in RequisicaoIA._meta.fields]


@admin.register(ConsumoIA)
class ConsumoIAAdmin(SomenteLeituraMixin, admin.ModelAdmin):
    list_display = ('dono', 'mes', 'tokens_total', 'custo_estimado', 'requisicoes')
    list_filter = ('mes',)
    search_fields = ('dono__username',)
    list_select_related = ('dono',)
    readonly_fields = [campo.name for campo in ConsumoIA._meta.fields]
