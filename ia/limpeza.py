from datetime import timedelta

from django.utils import timezone

from .models import ConfiguracaoIA, RequisicaoIA


LOTE_PADRAO = 1000


def apagar_requisicoes_antigas(lote=LOTE_PADRAO):
    """Apaga RequisicaoIA mais antigas que reter_requisicoes_dias. Não toca em ConsumoIA."""
    dias = ConfiguracaoIA.obter().reter_requisicoes_dias
    limite = timezone.now() - timedelta(days=dias)
    apagadas = 0
    while True:
        ids = list(
            RequisicaoIA.objects.filter(criado_em__lt=limite)
            .order_by('pk')
            .values_list('pk', flat=True)[:lote]
        )
        if not ids:
            return apagadas
        apagadas += RequisicaoIA.objects.filter(pk__in=ids).delete()[0]
