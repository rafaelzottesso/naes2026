from datetime import timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ia.cota import mes_atual
from ia.limpeza import apagar_requisicoes_antigas
from ia.models import ConfiguracaoIA, ConsumoIA, RequisicaoIA


class DadosLimpezaTestCase(TestCase):
    def setUp(self):
        cache.clear()
        config = ConfiguracaoIA.obter()
        config.reter_requisicoes_dias = 60
        config.save()
        self.usuario = get_user_model().objects.create_user('ana', password='senha-teste')
        ConsumoIA.objects.create(dono=self.usuario, mes=mes_atual(), tokens_total=999, requisicoes=3)
        self.antigas = [self._requisicao(dias=100) for _ in range(3)]
        self.recente = self._requisicao(dias=1)

    def _requisicao(self, dias):
        requisicao = RequisicaoIA.objects.create(
            usuario=self.usuario, finalidade='teste', provedor='falso', situacao='sucesso',
        )
        RequisicaoIA.objects.filter(pk=requisicao.pk).update(criado_em=timezone.now() - timedelta(days=dias))
        return requisicao


class LimpezaTests(DadosLimpezaTestCase):
    def test_apaga_so_requisicoes_alem_do_prazo(self):
        apagadas = apagar_requisicoes_antigas()

        self.assertEqual(apagadas, 3)
        self.assertEqual(list(RequisicaoIA.objects.values_list('pk', flat=True)), [self.recente.pk])

    def test_nao_toca_no_consumo(self):
        apagar_requisicoes_antigas()

        self.assertEqual(ConsumoIA.objects.get(dono=self.usuario, mes=mes_atual()).tokens_total, 999)

    def test_apaga_em_lotes_pequenos(self):
        apagadas = apagar_requisicoes_antigas(lote=2)

        self.assertEqual(apagadas, 3)
        self.assertEqual(RequisicaoIA.objects.count(), 1)

    def test_prazo_vem_da_configuracao(self):
        config = ConfiguracaoIA.obter()
        config.reter_requisicoes_dias = 200
        config.save()

        self.assertEqual(apagar_requisicoes_antigas(), 0)
        self.assertEqual(RequisicaoIA.objects.count(), 4)

    def test_comando_ia_limpar_informa_quantidade(self):
        saida = StringIO()

        call_command('ia_limpar', stdout=saida)

        self.assertIn('3 requisição(ões) apagada(s).', saida.getvalue())
        self.assertEqual(RequisicaoIA.objects.count(), 1)


class ManutencaoRotaTests(DadosLimpezaTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('ia:manutencao')

    def test_post_com_segredo_correto_apaga_e_responde_quantidade(self):
        with self.settings(TAREFAS_SEGREDO='segredo-teste'):
            resposta = self.client.post(self.url, headers={'X-Tarefas-Segredo': 'segredo-teste'})

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json(), {'apagadas': 3})
        self.assertEqual(RequisicaoIA.objects.count(), 1)

    def test_segredo_errado_recebe_403_e_nada_e_apagado(self):
        with self.settings(TAREFAS_SEGREDO='segredo-teste'):
            resposta = self.client.post(self.url, headers={'X-Tarefas-Segredo': 'errado'})

        self.assertEqual(resposta.status_code, 403)
        self.assertEqual(RequisicaoIA.objects.count(), 4)

    def test_sem_cabecalho_recebe_403(self):
        with self.settings(TAREFAS_SEGREDO='segredo-teste'):
            resposta = self.client.post(self.url)

        self.assertEqual(resposta.status_code, 403)
        self.assertEqual(RequisicaoIA.objects.count(), 4)

    def test_segredo_vazio_desliga_o_endpoint(self):
        with self.settings(TAREFAS_SEGREDO=''):
            resposta = self.client.post(self.url, headers={'X-Tarefas-Segredo': ''})

        self.assertEqual(resposta.status_code, 403)
        self.assertEqual(RequisicaoIA.objects.count(), 4)

    def test_get_nao_e_aceito(self):
        with self.settings(TAREFAS_SEGREDO='segredo-teste'):
            resposta = self.client.get(self.url, headers={'X-Tarefas-Segredo': 'segredo-teste'})

        self.assertEqual(resposta.status_code, 405)
        self.assertEqual(RequisicaoIA.objects.count(), 4)
