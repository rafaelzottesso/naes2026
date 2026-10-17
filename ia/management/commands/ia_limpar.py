from django.core.management.base import BaseCommand

from ia.limpeza import apagar_requisicoes_antigas


class Command(BaseCommand):
    help = 'Apaga requisições de IA mais antigas que reter_requisicoes_dias, em lotes de 1000.'

    def handle(self, *args, **options):
        apagadas = apagar_requisicoes_antigas()
        self.stdout.write(self.style.SUCCESS(f'{apagadas} requisição(ões) apagada(s).'))
