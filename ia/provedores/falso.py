from collections import deque

from ia.provedores.base import ProvedorIA, RespostaIA, UsoTokens


class ProvedorFalso(ProvedorIA):
    def __init__(self, config, acesso=None):
        super().__init__(config, acesso)
        self._fila = deque()
        self.pedidos = []

    def programar(self, texto='', dados=None, uso=None, erro=None):
        self._fila.append((texto, dados, uso, erro))

    def gerar(self, pedido):
        self.pedidos.append(pedido)
        texto, dados, uso, erro = self._fila.popleft() if self._fila else ('ok', None, None, None)
        if erro is not None:
            raise erro
        return RespostaIA(
            texto=texto,
            dados=dados,
            uso=uso or UsoTokens(),
            modelo=self.config.modelo,
            motivo_fim='STOP',
        )
