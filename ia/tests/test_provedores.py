from datetime import timedelta
from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone

from ia.models import ConfiguracaoIA
from ia.provedores import _cache, modo_de_acesso, obter_provedor
from ia.provedores.base import ErroConfiguracao, ErroTemporario, PedidoIA, UsoTokens
from ia.provedores.falso import ProvedorFalso


class ConfiguracaoIATests(TestCase):
    def setUp(self):
        cache.clear()
        _cache.clear()

    def test_obter_cria_linha_unica_e_reutiliza(self):
        primeira = ConfiguracaoIA.obter()
        cache.clear()
        segunda = ConfiguracaoIA.obter()
        self.assertEqual(primeira.pk, 1)
        self.assertEqual(segunda.pk, 1)
        self.assertEqual(ConfiguracaoIA.objects.count(), 1)

    def test_salvar_configuracao_gera_novo_provedor(self):
        config = ConfiguracaoIA.obter()
        config.provedor = 'falso'
        config.save()
        ConfiguracaoIA.objects.filter(pk=1).update(atualizado_em=timezone.now() - timedelta(minutes=5))
        cache.clear()
        provedor_antigo = obter_provedor(ConfiguracaoIA.obter())

        config = ConfiguracaoIA.obter()
        config.temperatura = Decimal('0.5')
        config.save()
        provedor_novo = obter_provedor(ConfiguracaoIA.obter())

        self.assertIsInstance(provedor_novo, ProvedorFalso)
        self.assertIsNot(provedor_antigo, provedor_novo)

    @override_settings(GOOGLE_GENAI_USE_ENTERPRISE=True, GOOGLE_CLOUD_PROJECT='')
    def test_gemini_enterprise_sem_projeto_levanta_erro_de_configuracao(self):
        config = ConfiguracaoIA.obter()
        config.provedor = 'gemini'
        config.save()
        with self.assertRaises(ErroConfiguracao) as contexto:
            obter_provedor(ConfiguracaoIA.obter())
        self.assertIn('GOOGLE_CLOUD_PROJECT', str(contexto.exception))


class ProvedorFalsoTests(TestCase):
    def setUp(self):
        self.provedor = ProvedorFalso(ConfiguracaoIA.obter())

    def test_responde_na_ordem_programada_e_registra_pedidos(self):
        self.provedor.programar(texto='um', uso=UsoTokens(entrada=3, saida=4))
        self.provedor.programar(texto='dois')
        pedido = PedidoIA(instrucoes='', texto='oi')

        primeira = self.provedor.gerar(pedido)
        segunda = self.provedor.gerar(pedido)
        terceira = self.provedor.gerar(pedido)

        self.assertEqual(primeira.texto, 'um')
        self.assertEqual(primeira.uso.total, 7)
        self.assertEqual(segunda.texto, 'dois')
        self.assertEqual(terceira.texto, 'ok')
        self.assertEqual(len(self.provedor.pedidos), 3)

    def test_levanta_erro_programado(self):
        self.provedor.programar(erro=ErroTemporario('instável'))
        with self.assertRaises(ErroTemporario) as contexto:
            self.provedor.gerar(PedidoIA(instrucoes='', texto='oi'))
        self.assertEqual(contexto.exception.situacao, 'erro_temporario')


class ModoDeAcessoTests(TestCase):
    @override_settings(GOOGLE_GENAI_USE_ENTERPRISE=False, GEMINI_API_KEY='', GOOGLE_CLOUD_PROJECT='')
    def test_sem_variaveis_escolhe_api_key_e_pede_a_chave(self):
        with self.assertRaises(ErroConfiguracao) as contexto:
            modo_de_acesso()
        self.assertIn('GEMINI_API_KEY', str(contexto.exception))

    @override_settings(GOOGLE_GENAI_USE_ENTERPRISE=False, GEMINI_API_KEY='chave-teste')
    def test_api_key_com_chave_devolve_o_modo_api_key(self):
        acesso = modo_de_acesso()
        self.assertEqual(acesso.modo, 'api_key')
        self.assertEqual(acesso.chave, 'chave-teste')

    @override_settings(GOOGLE_GENAI_USE_ENTERPRISE=True, GOOGLE_CLOUD_PROJECT='projeto-teste', GOOGLE_CLOUD_LOCATION='')
    def test_enterprise_com_projeto_usa_regiao_global_por_padrao(self):
        acesso = modo_de_acesso()
        self.assertEqual(acesso.modo, 'enterprise')
        self.assertEqual(acesso.projeto, 'projeto-teste')
        self.assertEqual(acesso.regiao, 'global')

    @override_settings(GOOGLE_GENAI_USE_ENTERPRISE=True, GOOGLE_CLOUD_PROJECT='', GEMINI_API_KEY='chave-teste')
    def test_enterprise_sem_projeto_levanta_erro_com_nome_da_variavel(self):
        with self.assertRaises(ErroConfiguracao) as contexto:
            modo_de_acesso()
        self.assertIn('GOOGLE_CLOUD_PROJECT', str(contexto.exception))
