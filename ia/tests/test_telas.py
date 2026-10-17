from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ia.cota import mes_atual
from ia.models import ConfiguracaoIA, ConfiguracaoIAUsuario, ConsumoIA, RequisicaoIA
from ia.provedores import _cache
from ia.provedores.base import IaIndisponivel


class TelasIATestCase(TestCase):
    def setUp(self):
        cache.clear()
        _cache.clear()
        self.admin = get_user_model().objects.create_superuser('admin', password='senha-teste')
        self.ana = get_user_model().objects.create_user('ana', password='senha-teste')
        self.bia = get_user_model().objects.create_user('bia', password='senha-teste')

    def _requisicao(self, usuario, **campos):
        dados = {
            'finalidade': 'teste',
            'provedor': 'falso',
            'situacao': 'sucesso',
            'tokens_total': 10,
            'custo_estimado': Decimal('0.01'),
        }
        dados.update(campos)
        return RequisicaoIA.objects.create(usuario=usuario, **dados)


class AcessoTelasTests(TelasIATestCase):
    def test_visitante_vai_ao_login(self):
        urls = [
            reverse('ia:requisicao-list'),
            reverse('ia:meu-consumo'),
            reverse('ia:configuracao'),
            reverse('ia:usuario-list'),
        ]
        for url in urls:
            with self.subTest(url=url):
                resposta = self.client.get(url)
                self.assertRedirects(resposta, f"{reverse('login')}?next={url}", fetch_redirect_response=False)

    def test_usuario_comum_recebe_403_nas_telas_admin(self):
        requisicao = self._requisicao(self.bia)
        self.client.force_login(self.ana)
        urls = [
            reverse('ia:requisicao-list'),
            reverse('ia:requisicao-detail', args=[requisicao.pk]),
            reverse('ia:configuracao'),
            reverse('ia:usuario-list'),
            reverse('ia:usuario-update', args=[self.bia.pk]),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_superusuario_acessa_telas_admin(self):
        requisicao = self._requisicao(self.ana)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('ia:requisicao-list')).status_code, 200)
        self.assertEqual(self.client.get(reverse('ia:requisicao-detail', args=[requisicao.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('ia:configuracao')).status_code, 200)
        self.assertEqual(self.client.get(reverse('ia:usuario-list')).status_code, 200)
        self.assertEqual(self.client.get(reverse('ia:usuario-update', args=[self.bia.pk])).status_code, 200)

    def test_menu_mostra_administracao_so_para_superusuario(self):
        self.client.force_login(self.ana)
        resposta = self.client.get(reverse('ia:meu-consumo'))
        self.assertContains(resposta, 'Meu consumo de IA')
        self.assertNotContains(resposta, 'Administração da IA')

        self.client.force_login(self.admin)
        resposta = self.client.get(reverse('ia:meu-consumo'))
        self.assertContains(resposta, 'Administração da IA')
        self.assertContains(resposta, reverse('ia:requisicao-list'))


class RequisicaoIAListTests(TelasIATestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)

    def test_filtra_por_situacao(self):
        sucesso = self._requisicao(self.ana, situacao='sucesso')
        erro = self._requisicao(self.ana, situacao='erro_temporario')

        resposta = self.client.get(reverse('ia:requisicao-list'), {'situacao': 'erro_temporario'})

        self.assertEqual(list(resposta.context['object_list']), [erro])
        self.assertNotIn(sucesso, resposta.context['object_list'])

    def test_resultado_erro_exclui_sucesso(self):
        sucesso = self._requisicao(self.ana, situacao='sucesso')
        erro = self._requisicao(self.bia, situacao='tempo_esgotado')

        resposta = self.client.get(reverse('ia:requisicao-list'), {'resultado': 'erro'})

        self.assertEqual(list(resposta.context['object_list']), [erro])
        self.assertNotIn(sucesso, resposta.context['object_list'])

    def test_filtra_por_periodo(self):
        antiga = self._requisicao(self.ana)
        RequisicaoIA.objects.filter(pk=antiga.pk).update(criado_em=timezone.now() - timedelta(days=400))
        recente = self._requisicao(self.ana)
        hoje = timezone.localdate().isoformat()

        resposta = self.client.get(reverse('ia:requisicao-list'), {'periodo_after': hoje, 'periodo_before': hoje})

        self.assertEqual(list(resposta.context['object_list']), [recente])

    def test_resumo_do_mes_ignora_filtros(self):
        self._requisicao(self.ana, situacao='sucesso', tokens_total=30)
        self._requisicao(self.bia, situacao='erro_permanente', tokens_total=20)

        resposta = self.client.get(reverse('ia:requisicao-list'), {'situacao': 'sucesso'})

        self.assertEqual(resposta.context['resumo']['tokens'], 50)
        self.assertEqual(resposta.context['resumo']['erros'], 1)

    def test_top_usuarios_ordenado_por_tokens(self):
        self._requisicao(self.ana, tokens_total=10)
        self._requisicao(self.bia, tokens_total=500)

        resposta = self.client.get(reverse('ia:requisicao-list'))

        nomes = [item['nome'] for item in resposta.context['top_usuarios']]
        self.assertEqual(nomes, ['bia', 'ana'])

    def test_detalhe_mostra_resposta(self):
        requisicao = self._requisicao(self.ana, resposta='texto-da-resposta-xyz')

        resposta = self.client.get(reverse('ia:requisicao-detail', args=[requisicao.pk]))

        self.assertContains(resposta, 'texto-da-resposta-xyz')


class MeuConsumoTests(TelasIATestCase):
    def test_exige_login(self):
        resposta = self.client.get(reverse('ia:meu-consumo'))
        self.assertEqual(resposta.status_code, 302)

    def test_mostra_so_o_consumo_do_proprio_usuario(self):
        ConsumoIA.objects.create(dono=self.ana, mes=mes_atual(), tokens_total=100, requisicoes=1)
        ConsumoIA.objects.create(dono=self.bia, mes=mes_atual(), tokens_total=900, requisicoes=1)
        self._requisicao(self.ana, finalidade='minha-tarefa')
        self._requisicao(self.bia, finalidade='tarefa-da-bia')
        self.client.force_login(self.ana)

        resposta = self.client.get(reverse('ia:meu-consumo'))

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context['situacao'].usado, 100)
        self.assertContains(resposta, 'minha-tarefa')
        self.assertNotContains(resposta, 'tarefa-da-bia')

    def test_mostra_aviso_quando_cota_esgotada(self):
        ConfiguracaoIAUsuario.objects.create(usuario=self.ana, limite_mensal=0)
        self.client.force_login(self.ana)

        resposta = self.client.get(reverse('ia:meu-consumo'))

        self.assertTrue(resposta.context['situacao'].esgotada)
        self.assertContains(resposta, 'Sua cota de IA acabou')


class ConfiguracaoIATests(TelasIATestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)
        self.dados = {
            'provedor': 'falso',
            'modelo': 'modelo-teste',
            'temperatura': '0.50',
            'max_tokens_saida': '4000',
            'nivel_raciocinio': 'low',
            'tentativas': '2',
            'timeout_s': '30',
            'limite_mensal_usuario': '5000',
            'aviso_percentual': '80',
            'reserva_minima_tokens': '1000',
            'limite_mensal_sistema': '0',
            'tamanho_maximo_mb': '10',
            'pdf_max_paginas': '10',
            'reter_requisicoes_dias': '60',
            'preco_entrada_milhao': '',
            'preco_saida_milhao': '',
        }

    def test_get_mostra_modo_de_acesso_somente_leitura(self):
        resposta = self.client.get(reverse('ia:configuracao'))

        self.assertContains(resposta, 'Modo de acesso')
        self.assertContains(resposta, 'Testar conexão')
        self.assertNotContains(resposta, 'name="modo_acesso"')

    def test_post_salva_configuracao(self):
        resposta = self.client.post(reverse('ia:configuracao'), self.dados)

        self.assertRedirects(resposta, reverse('ia:configuracao'))
        config = ConfiguracaoIA.obter()
        self.assertEqual(config.modelo, 'modelo-teste')
        self.assertEqual(config.limite_mensal_usuario, 5000)

    def test_testar_conexao_mostra_sucesso(self):
        with patch('ia.views.testar_conexao', return_value='Conexão OK. Teste.') as teste:
            resposta = self.client.post(reverse('ia:configuracao-testar'))

        teste.assert_called_once_with(self.admin)
        self.assertRedirects(resposta, reverse('ia:configuracao'))
        mensagens = [str(m) for m in get_messages(resposta.wsgi_request)]
        self.assertIn('Conexão OK. Teste.', mensagens)

    def test_testar_conexao_mostra_erro(self):
        with patch('ia.views.testar_conexao', side_effect=IaIndisponivel('IA desligada.')):
            resposta = self.client.post(reverse('ia:configuracao-testar'))

        mensagens = [str(m) for m in get_messages(resposta.wsgi_request)]
        self.assertTrue(any('Falha no teste de conexão' in m for m in mensagens))

    def test_testar_conexao_so_aceita_post(self):
        resposta = self.client.get(reverse('ia:configuracao-testar'))
        self.assertEqual(resposta.status_code, 405)

    def test_usuario_comum_nao_testa_conexao(self):
        self.client.force_login(self.ana)
        with patch('ia.views.testar_conexao') as teste:
            resposta = self.client.post(reverse('ia:configuracao-testar'))
        self.assertEqual(resposta.status_code, 403)
        teste.assert_not_called()


class UsuarioIATests(TelasIATestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)

    def test_lista_mostra_limite_padrao_e_uso(self):
        ConsumoIA.objects.create(dono=self.ana, mes=mes_atual(), tokens_total=300, requisicoes=1)
        ConfiguracaoIAUsuario.objects.create(usuario=self.bia, limite_mensal=1000)

        resposta = self.client.get(reverse('ia:usuario-list'))

        linhas = {linha['usuario'].username: linha for linha in resposta.context['linhas']}
        self.assertEqual(linhas['ana']['uso'], 300)
        self.assertEqual(linhas['ana']['origem'], 'padrão')
        self.assertFalse(linhas['ana']['tem_excecao'])
        self.assertEqual(linhas['bia']['limite'], 1000)
        self.assertEqual(linhas['bia']['origem'], 'próprio')

    def test_edita_excecao_do_usuario(self):
        resposta = self.client.post(reverse('ia:usuario-update', args=[self.bia.pk]), {
            'ia_habilitada': 'on',
            'limite_mensal': '500',
            'observacao': 'teste',
        })

        self.assertRedirects(resposta, reverse('ia:usuario-list'))
        configuracao = ConfiguracaoIAUsuario.objects.get(usuario=self.bia)
        self.assertEqual(configuracao.limite_mensal, 500)
        self.assertTrue(configuracao.ia_habilitada)

    def test_edita_desliga_ia_do_usuario(self):
        self.client.post(reverse('ia:usuario-update', args=[self.bia.pk]), {'observacao': ''})

        configuracao = ConfiguracaoIAUsuario.objects.get(usuario=self.bia)
        self.assertFalse(configuracao.ia_habilitada)

    def test_voltar_ao_padrao_apaga_excecao(self):
        ConfiguracaoIAUsuario.objects.create(usuario=self.bia, ia_habilitada=False, limite_mensal=10)

        resposta = self.client.post(reverse('ia:usuario-resetar', args=[self.bia.pk]))

        self.assertRedirects(resposta, reverse('ia:usuario-list'))
        self.assertFalse(ConfiguracaoIAUsuario.objects.filter(usuario=self.bia).exists())

    def test_voltar_ao_padrao_so_aceita_post(self):
        ConfiguracaoIAUsuario.objects.create(usuario=self.bia, limite_mensal=10)

        resposta = self.client.get(reverse('ia:usuario-resetar', args=[self.bia.pk]))

        self.assertEqual(resposta.status_code, 405)
        self.assertTrue(ConfiguracaoIAUsuario.objects.filter(usuario=self.bia).exists())
