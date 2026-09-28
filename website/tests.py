from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse


class IndexTests(TestCase):
	def test_visitante_ve_inicio_publico_e_menu_de_visitante(self):
		response = self.client.get(reverse('index'))

		self.assertContains(response, 'Seu dinheiro, em fluxo.')
		self.assertContains(response, reverse('login'))
		self.assertNotContains(response, reverse('financeiro-dashboard'))
		self.assertNotContains(response, reverse('lancamento-list'))

	def test_usuario_autenticado_ve_menu_financeiro(self):
		usuario = get_user_model().objects.create_user(username='menu-teste', password='senha-teste')
		self.client.force_login(usuario)

		response = self.client.get(reverse('index'))

		self.assertContains(response, reverse('financeiro-dashboard'))
		self.assertContains(response, reverse('lancamento-list'))
