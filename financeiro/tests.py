from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Categoria, Centro, FormaPagamento, Lancamento, Parcela, Pessoa
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

    def test_lista_de_parcelas_filtra_vencidas_nao_pagadas(self):
        hoje = timezone.localdate()
        self._post_lancamento(data=(hoje - timedelta(days=2)).isoformat(), descricao='Parcela vencida')
        vencida = Parcela.objects.get()
        self._post_lancamento(data=(hoje - timedelta(days=3)).isoformat(), descricao='Parcela paga')
        paga = Parcela.objects.get(lancamento__descricao='Parcela paga')
        Parcela.objects.filter(pk=paga.pk).update(
            data_pagamento=hoje - timedelta(days=1), valor_pago=paga.valor,
        )
        self._post_lancamento(data=hoje.isoformat(), descricao='Vence hoje')
        self._post_lancamento(data=(hoje + timedelta(days=2)).isoformat(), descricao='Vence depois')

        lista = self.client.get(reverse('parcela-list'))
        self.assertContains(lista, 'Parcela vencida')
        self.assertContains(lista, 'Parcela paga')

        vencimentos = self.client.get(reverse('parcela-list'), {'vencidas': 'true'})
        self.assertContains(vencimentos, 'Parcela vencida')
        self.assertNotContains(vencimentos, 'Parcela paga')
        self.assertNotContains(vencimentos, 'Vence hoje')
        self.assertNotContains(vencimentos, 'Vence depois')

    def test_lista_de_parcelas_respeita_o_dono_e_navbar_tem_atalhos(self):
        self._post_lancamento(descricao='Parcela privada')
        resposta = self.client.get(reverse('parcela-list'))
        self.assertContains(resposta, 'Parcela privada')
        self.assertContains(resposta, reverse('parcela-list') + '?vencidas=true')

        self.client.force_login(self.outro)
        resposta_outro = self.client.get(reverse('parcela-list'))
        self.assertNotContains(resposta_outro, 'Parcela privada')


    def test_grava_numero_centro_ir_e_agrupado(self):
        centro = Centro.objects.create(nome='Reforma', criado_por=self.user)
        self._post_lancamento(
            numero='NF-123', centro=centro.pk, declara_ir='on', agrupado='on',
        )
        lancamento = Lancamento.objects.get()
        self.assertEqual(lancamento.numero, 'NF-123')
        self.assertEqual(lancamento.centro, centro)
        self.assertTrue(lancamento.declara_ir)
        self.assertTrue(lancamento.agrupado)
        detalhe = self.client.get(reverse('lancamento-detail', args=[lancamento.pk]))
        self.assertContains(detalhe, 'Reforma')

    def test_centro_e_ir_sao_opcionais(self):
        self._post_lancamento()
        lancamento = Lancamento.objects.get()
        self.assertIsNone(lancamento.centro)
        self.assertFalse(lancamento.declara_ir)
        self.assertFalse(lancamento.agrupado)

    def test_centro_inativo_ou_de_outro_usuario_nao_e_aceito(self):
        inativo = Centro.objects.create(nome='Antigo', status=False, criado_por=self.user)
        alheio = Centro.objects.create(nome='Alheio', criado_por=self.outro)
        for centro in (inativo, alheio):
            resposta = self._post_lancamento(centro=centro.pk)
            self.assertEqual(resposta.status_code, 200)
        self.assertFalse(Lancamento.objects.exists())


class CentroTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='centro-dono', password='senha-teste')
        self.client.force_login(self.user)

    def test_cria_lista_e_exclui_centro(self):
        resposta = self.client.post(reverse('centro-create'), {'nome': 'Viagem', 'status': 'on'})
        self.assertRedirects(resposta, reverse('centro-list'))
        centro = Centro.objects.get()
        self.assertEqual(centro.criado_por, self.user)
        self.assertContains(self.client.get(reverse('centro-list')), 'Viagem')
        self.assertContains(self.client.get(reverse('centro-detail', args=[centro.pk])), 'Viagem')
        self.client.post(reverse('centro-delete', args=[centro.pk]))
        self.assertFalse(Centro.objects.exists())

    def test_outro_usuario_nao_ve_o_centro(self):
        centro = Centro.objects.create(nome='Privado', criado_por=self.user)
        outro = get_user_model().objects.create_user(username='centro-outro', password='senha-teste')
        self.client.force_login(outro)
        self.assertEqual(self.client.get(reverse('centro-detail', args=[centro.pk])).status_code, 404)
        self.assertNotContains(self.client.get(reverse('centro-list')), 'Privado')


class DocumentoDaPessoaTests(TestCase):
    dados = {
        'nome': 'Fornecedor', 'documento': '12345678901', 'cep': '87020000',
        'endereco': 'Rua A', 'cidade': 'Maringá', 'status': 'on',
    }

    def setUp(self):
        self.user = get_user_model().objects.create_user(username='doc-dono', password='senha-teste')
        self.outro = get_user_model().objects.create_user(username='doc-outro', password='senha-teste')
        self.client.force_login(self.user)

    def test_documento_repetido_no_mesmo_usuario_e_recusado(self):
        self.client.post(reverse('pessoa-create'), self.dados)
        resposta = self.client.post(reverse('pessoa-create'), self.dados)
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'já cadastrou')
        self.assertEqual(Pessoa.objects.count(), 1)

    def test_outro_usuario_pode_usar_o_mesmo_documento(self):
        self.client.post(reverse('pessoa-create'), self.dados)
        self.client.force_login(self.outro)
        resposta = self.client.post(reverse('pessoa-create'), self.dados)
        self.assertRedirects(resposta, reverse('pessoa-list'))
        self.assertEqual(Pessoa.objects.filter(documento='12345678901').count(), 2)


class TelasTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='telas', password='senha-teste')
        self.client.force_login(self.user)
        self.categoria = Categoria.objects.create(nome='Lazer', criado_por=self.user)
        self.pessoa = Pessoa.objects.create(
            nome='Loja', documento='11122233344', cep='87020000',
            endereco='Rua C', cidade='Maringá', criado_por=self.user,
        )
        self.forma = FormaPagamento.objects.create(nome='Cartão', criado_por=self.user)
        hoje = timezone.localdate()
        self.lancamento = Lancamento.objects.create(
            tipo='despesa', data=hoje - timedelta(days=40), categoria=self.categoria,
            pessoa=self.pessoa, forma_pagamento=self.forma, descricao='Notebook',
            valor=Decimal('300.00'), parcelas=3, intervalo_parcelas=30, criado_por=self.user,
        )
        from .services import gerar_parcelas
        gerar_parcelas(self.lancamento)
        primeira, segunda, terceira = self.lancamento.itens.order_by('numero')
        primeira.valor_pago = primeira.valor_liquido
        primeira.data_pagamento = hoje - timedelta(days=39)
        primeira.save()
        # segunda venceu há 10 dias e continua em aberto; terceira vence daqui a 20 dias

    def test_detalhe_mostra_cada_parcela_com_a_situacao_padrao(self):
        detalhe = self.client.get(reverse('lancamento-detail', args=[self.lancamento.pk]))
        self.assertContains(detalhe, 'fin-linha-paga')
        self.assertContains(detalhe, 'fin-linha-atrasada')
        self.assertContains(detalhe, 'fin-linha-a_vencer')
        self.assertContains(detalhe, 'text-bg-danger"><i class="bi bi-exclamation-octagon-fill me-1"></i>Vencida')
        self.assertContains(detalhe, 'text-bg-info"><i class="bi bi-hourglass-split me-1"></i>Em aberto')
        resumo = detalhe.context['resumo']
        self.assertEqual((resumo['qtd_pagas'], resumo['qtd_vencidas'], resumo['qtd_abertas']), (1, 1, 1))
        self.assertEqual(resumo['pago'], Decimal('100.00'))
        self.assertEqual(resumo['vencido'], Decimal('100.00'))

    def test_lista_de_lancamentos_mostra_situacao_e_valor(self):
        lista = self.client.get(reverse('lancamento-list'))
        self.assertContains(lista, 'Parcela vencida')
        self.assertContains(lista, '1/3 pagas')

    def test_todas_as_telas_abrem(self):
        centro = Centro.objects.create(nome='Reforma', criado_por=self.user)
        parcela = self.lancamento.itens.first()
        urls = [
            reverse('index'), reverse('financeiro-dashboard'), reverse('lancamento-list'),
            reverse('lancamento-create'), reverse('lancamento-update', args=[self.lancamento.pk]),
            reverse('lancamento-delete', args=[self.lancamento.pk]),
            reverse('parcela-detail', args=[parcela.pk]), reverse('parcela-update', args=[parcela.pk]),
            reverse('categoria-list'), reverse('categoria-detail', args=[self.categoria.pk]),
            reverse('categoria-create'), reverse('centro-list'),
            reverse('centro-detail', args=[centro.pk]), reverse('pessoa-list'),
            reverse('pessoa-detail', args=[self.pessoa.pk]), reverse('forma-pagamento-list'),
            reverse('forma-pagamento-detail', args=[self.forma.pk]), reverse('login'),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_editar_lancamento_grava_os_campos_cadastrais(self):
        resposta = self.client.post(reverse('lancamento-update', args=[self.lancamento.pk]), {
            'numero': 'NF-9', 'descricao': 'Notebook novo', 'tipo': 'despesa',
            'categoria': self.categoria.pk, 'pessoa': self.pessoa.pk,
            'forma_pagamento': self.forma.pk, 'declara_ir': 'on',
        })
        self.assertRedirects(resposta, reverse('lancamento-detail', args=[self.lancamento.pk]))
        self.lancamento.refresh_from_db()
        self.assertEqual((self.lancamento.numero, self.lancamento.descricao), ('NF-9', 'Notebook novo'))
        self.assertTrue(self.lancamento.declara_ir)
        self.assertEqual(self.lancamento.itens.count(), 3)


    def test_formularios_usam_botoes_padrao_com_carregando(self):
        for url in (reverse('categoria-create'), reverse('lancamento-create'), reverse('login')):
            with self.subTest(url=url):
                pagina = self.client.get(url)
                self.assertContains(pagina, 'fin-form-acoes')
                self.assertContains(pagina, 'data-texto-carregando')
                self.assertContains(pagina, 'js/carregando.js')
