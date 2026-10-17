from django.conf import settings
from django.utils.module_loading import import_string

from ia.provedores.base import AcessoIA, ErroConfiguracao

PROVEDORES = {
    'gemini': 'ia.provedores.gemini.ProvedorGemini',
    'falso': 'ia.provedores.falso.ProvedorFalso',
}

_cache = {}


def modo_de_acesso():
    if settings.GOOGLE_GENAI_USE_ENTERPRISE:
        if not settings.GOOGLE_CLOUD_PROJECT:
            raise ErroConfiguracao(
                'Falta a variável GOOGLE_CLOUD_PROJECT (GOOGLE_GENAI_USE_ENTERPRISE=true está ligado).'
            )
        return AcessoIA(
            modo='enterprise',
            projeto=settings.GOOGLE_CLOUD_PROJECT,
            regiao=settings.GOOGLE_CLOUD_LOCATION or 'global',
        )
    if not settings.GEMINI_API_KEY:
        raise ErroConfiguracao(
            'Falta a variável GEMINI_API_KEY (modo API Key). Para usar enterprise, defina GOOGLE_GENAI_USE_ENTERPRISE=true.'
        )
    return AcessoIA(modo='api_key', chave=settings.GEMINI_API_KEY)


def obter_provedor(config):
    caminho = PROVEDORES.get(config.provedor)
    if caminho is None:
        raise ErroConfiguracao(f'Provedor de IA desconhecido: {config.provedor}')
    acesso = modo_de_acesso() if config.provedor == 'gemini' else None
    modo = acesso.modo if acesso else ''
    assinatura = (config.provedor, config.atualizado_em, modo)
    if _cache.get('assinatura') != assinatura:
        provedor = import_string(caminho)(config, acesso)
        _cache.clear()
        _cache.update(assinatura=assinatura, provedor=provedor)
    return _cache['provedor']
