from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Categoria, FormaPagamento, Lancamento, Parcela, Pessoa
from .services import dividir_valor


class PessoaTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='financeiro-teste', password='senha-teste')
        self.client.force_login(self.user)

    def test_cria_pessoa_e_exibe_na_lista(self):
        response = self.client.post(reverse('pessoa-create'), {
            'nome': 'Fornecedor Exemplo',
            'documento': '12345678000199',
            'cep': '12345678',
            'endereco': 'Rua Central, 10',
            'cidade': 'São Paulo',
            'status': 'on',
        })

        self.assertRedirects(response, reverse('pessoa-list'))
        pessoa = Pessoa.objects.get(documento='12345678000199')
        self.assertEqual(pessoa.criado_por, self.user)
        lista = self.client.get(reverse('pessoa-list'))
        self.assertContains(lista, 'Fornecedor Exemplo')

    def test_pessoa_e_obrigatoria_no_formulario_de_lancamento(self):
        response = self.client.get(reverse('lancamento-create'))

        self.assertTrue(response.context['form'].fields['pessoa'].required)

    def test_menu_website_tem_links_de_cadastro_e_listagem(self):
        response = self.client.get(reverse('index'))

        self.assertContains(response, reverse('pessoa-create'))
        self.assertContains(response, reverse('pessoa-list'))

    def test_outro_usuario_nao_ve_a_pessoa(self):
        Pessoa.objects.create(
            nome='Somente minha',
            documento='12345678901',
            cep='87020000',
            endereco='Rua A',
            cidade='Maringá',
            criado_por=self.user,
        )
        outro = get_user_model().objects.create_user(username='outro-pessoa', password='senha-teste')
        self.client.force_login(outro)
        lista = self.client.get(reverse('pessoa-list'))
        self.assertNotContains(lista, 'Somente minha')


class LancamentoParcelasTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='dono', password='senha-teste')
        self.outro = get_user_model().objects.create_user(username='vizinho', password='senha-teste')
        self.client.force_login(self.user)
        self.categoria = Categoria.objects.create(nome='Moradia', criado_por=self.user)
        self.pessoa = Pessoa.objects.create(
            nome='Imobiliária',
            documento='10987654000199',
            cep='87020000',
            endereco='Rua B, 1',
            cidade='Maringá',
            criado_por=self.user,
        )
        self.forma = FormaPagamento.objects.create(nome='Pix', criado_por=self.user)
        self.boleto = FormaPagamento.objects.create(nome='Boleto', criado_por=self.user)

    def _post_lancamento(self, **extras):
        dados = {
            'tipo': 'despesa',
            'data': '2026-09-10',
            'categoria': self.categoria.pk,
            'pessoa': self.pessoa.pk,
            'forma_pagamento': self.forma.pk,
            'descricao': 'Aluguel',
            'valor': '100.00',
            'desconto': '0',
            'acrescimo': '0',
            'parcelas': '1',
            'status': 'on',
        }
        dados.update(extras)
        return self.client.post(reverse('lancamento-create'), dados)

    def test_a_vista_gera_uma_parcela_com_a_mesma_forma(self):
        resposta = self._post_lancamento()
        lancamento = Lancamento.objects.get(descricao='Aluguel')
        self.assertRedirects(resposta, reverse('lancamento-detail', args=[lancamento.pk]))
        parcelas = list(lancamento.itens.all())
        self.assertEqual(len(parcelas), 1)
        self.assertEqual(parcelas[0].valor, Decimal('100.00'))
        self.assertEqual(parcelas[0].forma_pagamento, self.forma)
        self.assertEqual(parcelas[0].data, lancamento.data)

    def test_divide_o_valor_e_a_ultima_parcela_fica_com_o_resto(self):
        self.assertEqual(dividir_valor(Decimal('100.00'), 3), [
            Decimal('33.33'), Decimal('33.33'), Decimal('33.34'),
        ])
        self._post_lancamento(parcelas='3', intervalo_parcelas='30', valor='100.00')
        lancamento = Lancamento.objects.get()
        valores = list(lancamento.itens.order_by('numero').values_list('valor', flat=True))
        self.assertEqual(valores, [Decimal('33.33'), Decimal('33.33'), Decimal('33.34')])
        self.assertEqual(sum(valores), lancamento.valor_total)
        self.assertEqual(
            lancamento.itens.get(numero=2).data,
            lancamento.data + timedelta(days=30),
        )

    def test_rejeita_zero_parcelas_e_intervalo_faltando(self):
        sem_parcela = self._post_lancamento(parcelas='0')
        self.assertEqual(sem_parcela.status_code, 200)
        self.assertFalse(Lancamento.objects.exists())

        sem_intervalo = self._post_lancamento(parcelas='4')
        self.assertEqual(sem_intervalo.status_code, 200)
        self.assertContains(sem_intervalo, 'intervalo')

    def test_desconto_maior_que_o_valor_nao_grava(self):
        resposta = self._post_lancamento(valor='10.00', desconto='50.00')
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(Lancamento.objects.exists())

    def test_excluir_lancamento_exclui_as_parcelas(self):
        self._post_lancamento(parcelas='2', intervalo_parcelas='15')
        lancamento = Lancamento.objects.get()
        self.assertEqual(Parcela.objects.count(), 2)
        resposta = self.client.post(reverse('lancamento-delete', args=[lancamento.pk]))
        self.assertRedirects(resposta, reverse('lancamento-list'))
        self.assertFalse(Lancamento.objects.exists())
        self.assertFalse(Parcela.objects.exists())

    def test_parcela_nao_tem_rota_de_exclusao_e_pode_trocar_a_forma(self):
        self._post_lancamento()
        parcela = Parcela.objects.get()
        resposta = self.client.get(f'/financeiro/excluir/parcela/{parcela.pk}/')
        self.assertEqual(resposta.status_code, 404)

        edicao = self.client.post(reverse('parcela-update', args=[parcela.pk]), {
            'data': '2026-09-10',
            'forma_pagamento': self.boleto.pk,
            'valor': '100.00',
            'desconto': '0',
            'acrescimo': '0',
            'valor_pago': '100.00',
            'data_pagamento': '2026-09-12',
            'status': 'on',
        })
        self.assertRedirects(edicao, reverse('lancamento-detail', args=[parcela.lancamento_id]))
        parcela.refresh_from_db()
        self.assertEqual(parcela.forma_pagamento, self.boleto)
        self.assertTrue(parcela.quitada)

    def test_pagamento_exige_valor_e_data_juntos(self):
        self._post_lancamento()
        parcela = Parcela.objects.get()
        resposta = self.client.post(reverse('parcela-update', args=[parcela.pk]), {
            'data': '2026-09-10',
            'forma_pagamento': self.forma.pk,
            'valor': '100.00',
            'valor_pago': '100.00',
            'status': 'on',
        })
        self.assertEqual(resposta.status_code, 200)
        parcela.refresh_from_db()
        self.assertIsNone(parcela.valor_pago)

    def test_outro_usuario_nao_ve_o_lancamento(self):
        self._post_lancamento()
        lancamento = Lancamento.objects.get()
        self.client.force_login(self.outro)
        detalhe = self.client.get(reverse('lancamento-detail', args=[lancamento.pk]))
        self.assertEqual(detalhe.status_code, 404)
        lista = self.client.get(reverse('lancamento-list'))
        self.assertNotContains(lista, 'Aluguel')
        inicio = self.client.get(reverse('index'))
        self.assertContains(inicio, 'Nenhum lançamento cadastrado ainda')

    def test_detalhe_mostra_as_parcelas(self):
        self._post_lancamento(parcelas='2', intervalo_parcelas='10', descricao='Condomínio')
        lancamento = Lancamento.objects.get(descricao='Condomínio')
        detalhe = self.client.get(reverse('lancamento-detail', args=[lancamento.pk]))
        self.assertContains(detalhe, 'Parcela 1')
        self.assertContains(detalhe, 'Parcela 2')
        self.assertContains(detalhe, reverse('parcela-update', args=[lancamento.itens.get(numero=1).pk]))
        self.assertNotContains(detalhe, 'excluir/parcela')
