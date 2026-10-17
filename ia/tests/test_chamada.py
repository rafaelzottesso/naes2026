from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase

from ia.chamada import chamar_ia
from ia.cota import CotaExcedida, limite_do_usuario, mes_atual, situacao_da_cota
from ia.models import ConfiguracaoIA, ConfiguracaoIAUsuario, ConsumoIA, RequisicaoIA
from ia.provedores import _cache, obter_provedor
from ia.provedores.base import ErroConfiguracao, ErroTemporario, IaIndisponivel, PedidoIA, UsoTokens


def _montar(config):
    return PedidoIA(instrucoes='', texto='oi')


class ChamadaIATests(TestCase):
    def setUp(self):
        cache.clear()
        _cache.clear()
        self.config = ConfiguracaoIA.obter()
        self.config.provedor = 'falso'
        self.config.tentativas = 2
        self.config.save()
        self.usuario = get_user_model().objects.create_user('ana', password='segredo-123')

    def _provedor(self):
        return obter_provedor(ConfiguracaoIA.obter())

    def _chamar(self, **kwargs):
        return chamar_ia(finalidade='teste', montar_pedido=_montar, usuario=self.usuario, **kwargs)

    def test_sucesso_grava_requisicao_com_referencia_e_soma_consumo(self):
        self._provedor().programar(texto='pronto', uso=UsoTokens(entrada=10, saida=5))

        resposta = self._chamar(referencia=self.usuario)

        self.assertEqual(resposta.texto, 'pronto')
        requisicao = RequisicaoIA.objects.get()
        self.assertEqual(requisicao.situacao, 'sucesso')
        self.assertEqual(requisicao.referencia, self.usuario)
        self.assertEqual(requisicao.tokens_total, 15)
        consumo = ConsumoIA.objects.get(dono=self.usuario, mes=mes_atual())
        self.assertEqual(consumo.tokens_total, 15)
        self.assertEqual(consumo.requisicoes, 1)

    @patch('ia.chamada.time.sleep')
    def test_erro_temporario_seguido_de_sucesso_grava_duas_linhas(self, sleep):
        provedor = self._provedor()
        provedor.programar(erro=ErroTemporario('instável', uso=UsoTokens(entrada=3)))
        provedor.programar(texto='ok', uso=UsoTokens(entrada=2, saida=1))

        self._chamar()

        linhas = list(RequisicaoIA.objects.order_by('tentativa').values_list('tentativa', 'situacao'))
        self.assertEqual(linhas, [(1, 'erro_temporario'), (2, 'sucesso')])
        sleep.assert_called_once_with(1)
        self.assertEqual(ConsumoIA.objects.get(dono=self.usuario, mes=mes_atual()).tokens_total, 6)

    @patch('ia.chamada.time.sleep')
    def test_erro_de_configuracao_nao_repete(self, sleep):
        provedor = self._provedor()
        provedor.programar(erro=ErroConfiguracao('sem chave'))

        with self.assertRaises(ErroConfiguracao):
            self._chamar()

        self.assertEqual(len(provedor.pedidos), 1)
        self.assertEqual(RequisicaoIA.objects.get().situacao, 'erro_configuracao')
        sleep.assert_not_called()

    def test_cota_esgotada_nao_chama_o_provedor(self):
        provedor = self._provedor()
        ConsumoIA.objects.create(dono=self.usuario, mes=mes_atual(), tokens_total=100000)

        with self.assertRaises(CotaExcedida):
            self._chamar()

        self.assertEqual(provedor.pedidos, [])
        self.assertEqual(RequisicaoIA.objects.get().situacao, 'bloqueada_cota')

    def test_limite_proprio_zero_bloqueia(self):
        ConfiguracaoIAUsuario.objects.create(usuario=self.usuario, limite_mensal=0)
        provedor = self._provedor()

        with self.assertRaises(CotaExcedida):
            self._chamar()

        self.assertEqual(provedor.pedidos, [])

    def test_limite_proprio_vazio_volta_ao_padrao(self):
        ConfiguracaoIAUsuario.objects.create(usuario=self.usuario, limite_mensal=None)
        self.assertEqual(limite_do_usuario(self.usuario), self.config.limite_mensal_usuario)

        self.config.limite_mensal_usuario = 500
        self.config.save()
        self.assertEqual(limite_do_usuario(self.usuario), 500)

    def test_ia_desligada_para_o_usuario_nao_chama_o_provedor(self):
        ConfiguracaoIAUsuario.objects.create(usuario=self.usuario, ia_habilitada=False)
        provedor = self._provedor()

        with self.assertRaises(IaIndisponivel):
            self._chamar()

        self.assertEqual(provedor.pedidos, [])
        self.assertEqual(RequisicaoIA.objects.get().situacao, 'indisponivel')

    def test_falha_ao_gravar_auditoria_nao_derruba_a_chamada(self):
        self._provedor().programar(texto='ok', uso=UsoTokens(entrada=1))

        with patch('ia.chamada.RequisicaoIA.objects.create', side_effect=Exception('banco indisponível')):
            with self.assertLogs('ia.chamada', level='ERROR'):
                resposta = self._chamar()

        self.assertEqual(resposta.texto, 'ok')

    def test_teto_do_sistema_bloqueia_todos(self):
        outro = get_user_model().objects.create_user('bruno', password='segredo-123')
        self.config.limite_mensal_sistema = 100
        self.config.save()
        ConsumoIA.objects.create(dono=outro, mes=mes_atual(), tokens_total=100)
        provedor = self._provedor()

        for usuario in (self.usuario, outro):
            with self.subTest(usuario=usuario.username):
                with self.assertRaises(IaIndisponivel):
                    chamar_ia(finalidade='teste', montar_pedido=_montar, usuario=usuario)

        self.assertEqual(provedor.pedidos, [])
        self.assertEqual(RequisicaoIA.objects.filter(situacao='indisponivel').count(), 2)

    def test_consumo_de_mes_anterior_nao_conta(self):
        mes_passado = (mes_atual() - timedelta(days=1)).replace(day=1)
        ConsumoIA.objects.create(dono=self.usuario, mes=mes_passado, tokens_total=100000)

        self.assertEqual(situacao_da_cota(self.usuario).usado, 0)
        self._provedor().programar(texto='ok')
        self.assertEqual(self._chamar().texto, 'ok')
