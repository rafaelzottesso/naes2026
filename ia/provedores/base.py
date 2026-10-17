from abc import ABC, abstractmethod
from dataclasses import dataclass

import pydantic


@dataclass(frozen=True)
class Arquivo:
    conteudo: bytes
    mime: str
    nome: str = ''


@dataclass(frozen=True)
class MensagemHistorico:
    papel: str
    texto: str

    def __post_init__(self):
        if self.papel not in ('user', 'model'):
            raise ValueError(f'Papel inválido: {self.papel!r}')


@dataclass(frozen=True)
class PedidoIA:
    instrucoes: str
    texto: str
    arquivos: tuple[Arquivo, ...] = ()
    historico: tuple[MensagemHistorico, ...] = ()
    esquema: type[pydantic.BaseModel] | None = None


@dataclass(frozen=True)
class UsoTokens:
    entrada: int = 0
    saida: int = 0
    raciocinio: int = 0

    @property
    def total(self):
        return self.entrada + self.saida


@dataclass(frozen=True)
class RespostaIA:
    texto: str
    dados: pydantic.BaseModel | None
    uso: UsoTokens
    modelo: str
    motivo_fim: str
    id_resposta: str = ''


@dataclass(frozen=True)
class AcessoIA:
    modo: str
    chave: str = ''
    projeto: str = ''
    regiao: str = ''


class ErroIA(Exception):
    situacao = 'erro'

    def __init__(self, mensagem='', *, uso=None, texto_bruto='', modelo=''):
        super().__init__(mensagem)
        self.uso = uso or UsoTokens()
        self.texto_bruto = texto_bruto
        self.modelo = modelo


class ErroTemporario(ErroIA):
    situacao = 'erro_temporario'


class TempoEsgotado(ErroTemporario):
    situacao = 'tempo_esgotado'


class ErroPermanente(ErroIA):
    situacao = 'erro_permanente'


class RespostaInvalida(ErroIA):
    situacao = 'resposta_invalida'

    def __init__(self, mensagem='', *, motivo_fim='', **kwargs):
        super().__init__(mensagem, **kwargs)
        self.motivo_fim = motivo_fim


class BloqueioSeguranca(ErroIA):
    situacao = 'bloqueada_seguranca'


class ErroConfiguracao(ErroIA):
    situacao = 'erro_configuracao'


class IaIndisponivel(ErroIA):
    situacao = 'indisponivel'


class ProvedorIA(ABC):
    def __init__(self, config, acesso=None):
        self.config = config
        self.acesso = acesso

    @abstractmethod
    def gerar(self, pedido: PedidoIA) -> RespostaIA:
        """Envia o pedido ao provedor e devolve a resposta normalizada."""
