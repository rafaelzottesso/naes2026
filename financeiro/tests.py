from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Pessoa


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
