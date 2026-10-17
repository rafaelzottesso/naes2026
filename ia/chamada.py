import logging
import time
from dataclasses import dataclass
from hashlib import sha256

import pydantic
from django.contrib.contenttypes.models import ContentType

from ia.arquivos import hash_arquivo
from ia.cota import (
    CotaExcedida,
    custo_estimado,
    dono_da_cota,
    registrar_consumo,
    teto_do_sistema_atingido,
    verificar,
)
from ia.models import ConfiguracaoIA, ConfiguracaoIAUsuario, RequisicaoIA
from ia.provedores import modo_de_acesso, obter_provedor
from ia.provedores.base import ErroIA, ErroTemporario, IaIndisponivel, PedidoIA, UsoTokens

logger = logging.getLogger(__name__)
RESPOSTA_MAX_CARACTERES = 20000


class _EsquemaTeste(pydantic.BaseModel):
    status: str


@dataclass
class _Chamada:
    usuario: object
    origem: str
    finalidade: str
    referencia: object
    versao_prompt: str
    config: ConfiguracaoIA
    contexto_hash: str = ''
    arquivo: dict | None = None


def chamar_ia(*, finalidade, montar_pedido, usuario, origem='site', referencia=None, versao_prompt='',
              arquivo_info=None):
    config = ConfiguracaoIA.obter()
    chamada = _Chamada(
        usuario=usuario, origem=origem, finalidade=finalidade, referencia=referencia,
        versao_prompt=versao_prompt, config=config,
    )

    if ConfiguracaoIAUsuario.objects.filter(usuario=usuario, ia_habilitada=False).exists():
        erro = IaIndisponivel('A IA está desligada para o seu usuário.')
        _auditar(chamada, tentativa=1, situacao=erro.situacao, erro=str(erro))
        raise erro

    if teto_do_sistema_atingido():
        erro = IaIndisponivel('O limite de uso de IA do sistema foi atingido neste mês.')
        _auditar(chamada, tentativa=1, situacao=erro.situacao, erro=str(erro))
        raise erro

    try:
        verificar(dono_da_cota(usuario))
    except CotaExcedida as cota:
        _auditar(chamada, tentativa=1, situacao='bloqueada_cota', erro=str(cota))
        raise

    pedido = montar_pedido(config)
    chamada.contexto_hash = _hash_contexto(pedido)
    chamada.arquivo = _info_arquivo(pedido, arquivo_info)

    try:
        provedor = obter_provedor(config)
    except ErroIA as erro:
        _auditar(chamada, tentativa=1, situacao=erro.situacao, erro=str(erro))
        raise

    tentativas = max(config.tentativas, 1)
    for numero in range(1, tentativas + 1):
        inicio = time.perf_counter()
        try:
            resposta = provedor.gerar(pedido)
        except ErroIA as erro:
            _auditar(
                chamada, tentativa=numero, situacao=erro.situacao, uso=erro.uso,
                duracao_ms=_duracao_ms(inicio), motivo_fim=getattr(erro, 'motivo_fim', ''),
                resposta=erro.texto_bruto, erro=str(erro),
            )
            _consumir(chamada, erro.uso)
            if isinstance(erro, ErroTemporario) and numero < tentativas:
                time.sleep(numero)
                continue
            raise
        _auditar(
            chamada, tentativa=numero, situacao='sucesso', uso=resposta.uso,
            duracao_ms=_duracao_ms(inicio), motivo_fim=resposta.motivo_fim, resposta=resposta.texto,
        )
        _consumir(chamada, resposta.uso)
        return resposta


def testar_conexao(usuario):
    def montar_pedido(config):
        return PedidoIA(
            instrucoes='Responda apenas com o JSON pedido.',
            texto='Responda com status "ok".',
            esquema=_EsquemaTeste,
        )

    chamar_ia(finalidade='teste_conexao', montar_pedido=montar_pedido, usuario=usuario)
    config = ConfiguracaoIA.obter()
    if config.provedor != 'gemini':
        return f'Conexão OK com o provedor {config.provedor}.'
    acesso = modo_de_acesso()
    if acesso.modo == 'enterprise':
        return f'Conexão OK. Modo Enterprise (projeto {acesso.projeto}, região {acesso.regiao}).'
    return 'Conexão OK. Modo API Key.'


def _auditar(chamada, *, tentativa, situacao, uso=None, duracao_ms=0, motivo_fim='', resposta='', erro=''):
    uso = uso or UsoTokens()
    try:
        arquivo = chamada.arquivo or {}
        campos = {
            'usuario': chamada.usuario,
            'origem': chamada.origem,
            'finalidade': chamada.finalidade,
            'provedor': chamada.config.provedor,
            'modelo': chamada.config.modelo,
            'versao_prompt': chamada.versao_prompt,
            'tentativa': tentativa,
            'situacao': situacao,
            'tokens_entrada': uso.entrada,
            'tokens_saida': uso.saida,
            'tokens_raciocinio': uso.raciocinio,
            'tokens_total': uso.total,
            'custo_estimado': custo_estimado(uso, chamada.config),
            'duracao_ms': duracao_ms,
            'motivo_fim': motivo_fim,
            'arquivo_mime': arquivo.get('mime', ''),
            'arquivo_tamanho': arquivo.get('tamanho'),
            'arquivo_hash': arquivo.get('hash', ''),
            'resposta': resposta[:RESPOSTA_MAX_CARACTERES],
            'erro': erro,
            'contexto_hash': chamada.contexto_hash,
        }
        if chamada.referencia is not None:
            campos['referencia_tipo'] = ContentType.objects.get_for_model(chamada.referencia)
            campos['referencia_id'] = chamada.referencia.pk
        RequisicaoIA.objects.create(**campos)
    except Exception:
        logger.exception('Falha ao gravar a auditoria da IA (finalidade %s).', chamada.finalidade)


def _consumir(chamada, uso):
    if uso.total:
        registrar_consumo(dono_da_cota(chamada.usuario), uso, custo_estimado(uso, chamada.config))


def _hash_contexto(pedido):
    textos = [pedido.instrucoes, *(mensagem.texto for mensagem in pedido.historico), pedido.texto]
    return sha256('\n'.join(textos).encode('utf-8')).hexdigest()


def _info_arquivo(pedido, arquivo_info):
    if arquivo_info is not None:
        return arquivo_info
    if pedido.arquivos:
        primeiro = pedido.arquivos[0]
        return {'mime': primeiro.mime, 'tamanho': len(primeiro.conteudo), 'hash': hash_arquivo(primeiro.conteudo)}
    return None


def _duracao_ms(inicio):
    return int((time.perf_counter() - inicio) * 1000)
