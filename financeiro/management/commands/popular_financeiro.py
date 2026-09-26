from calendar import monthrange
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from financeiro.models import Categoria, FormaPagamento, Lancamento, Pessoa
from financeiro.services import gerar_parcelas


CATEGORIAS = [
    ('Salário', 'Remuneração do trabalho.'),
    ('Renda extra', 'Freelas e vendas eventuais.'),
    ('Rendimentos', 'Juros e dividendos.'),
    ('Moradia', 'Aluguel e manutenção da casa.'),
    ('Contas da casa', 'Água, energia, internet e telefone.'),
    ('Alimentação', 'Supermercado, feira e restaurante.'),
    ('Transporte', 'Combustível e transporte.'),
    ('Saúde', 'Plano, consultas e farmácia.'),
    ('Educação', 'Mensalidades e cursos.'),
    ('Lazer', 'Passeios e compras eventuais.'),
    ('Vestuário e cuidados pessoais', 'Roupas e higiene.'),
    ('Dívidas e empréstimos', 'Parcelas de empréstimo e cartão.'),
    ('Impostos e taxas', 'Impostos e tarifas.'),
    ('Assinaturas', 'Streaming e aplicativos.'),
]

FORMAS = [
    ('Pix', 'Transferência instantânea.'),
    ('Boleto', 'Pagamento com código de barras.'),
    ('Cartão de crédito', 'Compra parcelada ou à vista no crédito.'),
    ('Cartão de débito', 'Débito na conta na hora da compra.'),
    ('Dinheiro', 'Pagamento em espécie.'),
    ('Transferência bancária', 'TED ou DOC.'),
]

PESSOAS = [
    ('Empresa Alfa Ltda', '11.222.333/0001-81', '87020-000', 'Av. Brasil, 100', 'Maringá'),
    ('Mercado Central', '22.333.444/0001-90', '87010-010', 'Rua das Flores, 50', 'Maringá'),
    ('Imobiliária Horizonte', '33.444.555/0001-08', '87015-200', 'Rua Joubert de Carvalho, 800', 'Maringá'),
    ('Companhia de Energia', '44.555.666/0001-17', '87020-100', 'Av. Colombo, 5000', 'Maringá'),
    ('Loja Tech', '55.666.777/0001-26', '01310-100', 'Av. Paulista, 1000', 'São Paulo'),
    ('Academia Movimento', '66.777.888/0001-35', '80010-000', 'Rua XV de Novembro, 300', 'Curitiba'),
    ('Operadora Conecta', '77.888.999/0001-44', '20040-020', 'Av. Rio Branco, 200', 'Rio de Janeiro'),
    ('Estúdio Norte', '88.999.000/0001-53', '30130-000', 'Rua da Bahia, 1200', 'Belo Horizonte'),
]


def deslocar_meses(data, meses):
    mes_zero = data.month - 1 + meses
    ano = data.year + mes_zero // 12
    mes = mes_zero % 12 + 1
    dia = min(data.day, monthrange(ano, mes)[1])
    return data.replace(year=ano, month=mes, day=dia)


class Command(BaseCommand):
    help = 'Cria categorias, pessoas, formas de pagamento e lançamentos de exemplo para o usuário admin.'

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        try:
            admin = User.objects.get(username='admin')
        except User.DoesNotExist as erro:
            raise CommandError('Crie o usuário "admin" antes de popular o financeiro.') from erro

        hoje = timezone.localdate()
        categorias = {
            nome: Categoria.objects.get_or_create(
                nome=nome,
                criado_por=admin,
                defaults={'descricao': descricao, 'status': True},
            )[0]
            for nome, descricao in CATEGORIAS
        }
        formas = {
            nome: FormaPagamento.objects.get_or_create(
                nome=nome,
                criado_por=admin,
                defaults={'descricao': descricao, 'status': True},
            )[0]
            for nome, descricao in FORMAS
        }
        pessoas = {}
        for nome, documento, cep, endereco, cidade in PESSOAS:
            pessoas[nome], _ = Pessoa.objects.get_or_create(
                documento=documento,
                defaults={
                    'nome': nome,
                    'cep': cep,
                    'endereco': endereco,
                    'cidade': cidade,
                    'status': True,
                    'criado_por': admin,
                },
            )

        planos = self._planos(hoje, categorias, formas, pessoas)
        criados = 0
        for plano in planos:
            pagamentos = plano.pop('pagamentos')
            troca_forma = plano.pop('troca_forma', {})
            lancamento, novo = Lancamento.objects.get_or_create(
                criado_por=admin,
                descricao=plano['descricao'],
                defaults=plano,
            )
            if not novo:
                continue
            gerar_parcelas(lancamento)
            for numero, data_pagamento in pagamentos.items():
                parcela = lancamento.itens.get(numero=numero)
                if numero in troca_forma:
                    parcela.forma_pagamento = troca_forma[numero]
                parcela.valor_pago = parcela.valor_liquido
                parcela.data_pagamento = data_pagamento
                parcela.save()
            criados += 1

        self.stdout.write(self.style.SUCCESS(
            f'Pronto para {admin.username}: {criados} lançamento(s) novo(s). '
            f'Categorias {len(categorias)}, pessoas {len(pessoas)}, formas {len(formas)}.'
        ))

    def _planos(self, hoje, categorias, formas, pessoas):
        pix = formas['Pix']
        boleto = formas['Boleto']
        credito = formas['Cartão de crédito']
        transferencia = formas['Transferência bancária']
        return [
            {
                'descricao': 'Salário do mês',
                'tipo': 'receita',
                'data': hoje.replace(day=5),
                'categoria': categorias['Salário'],
                'pessoa': pessoas['Empresa Alfa Ltda'],
                'forma_pagamento': pix,
                'valor': Decimal('6500.00'),
                'parcelas': 1,
                'pagamentos': {1: hoje.replace(day=5)},
            },
            {
                'descricao': 'Salário do mês anterior',
                'tipo': 'receita',
                'data': deslocar_meses(hoje.replace(day=5), -1),
                'categoria': categorias['Salário'],
                'pessoa': pessoas['Empresa Alfa Ltda'],
                'forma_pagamento': pix,
                'valor': Decimal('6500.00'),
                'parcelas': 1,
                'pagamentos': {1: deslocar_meses(hoje.replace(day=5), -1)},
            },
            {
                'descricao': 'Rendimento da aplicação',
                'tipo': 'receita',
                'data': deslocar_meses(hoje.replace(day=15), -4),
                'categoria': categorias['Rendimentos'],
                'pessoa': pessoas['Empresa Alfa Ltda'],
                'forma_pagamento': transferencia,
                'valor': Decimal('180.50'),
                'parcelas': 1,
                'pagamentos': {1: deslocar_meses(hoje.replace(day=15), -4)},
            },
            {
                'descricao': 'Freelance de design',
                'tipo': 'receita',
                'data': deslocar_meses(hoje.replace(day=20), -1),
                'categoria': categorias['Renda extra'],
                'pessoa': pessoas['Estúdio Norte'],
                'forma_pagamento': transferencia,
                'valor': Decimal('1200.00'),
                'parcelas': 1,
                'pagamentos': {1: deslocar_meses(hoje.replace(day=20), -1)},
            },
            {
                'descricao': 'Aluguel do apartamento',
                'tipo': 'despesa',
                'data': hoje.replace(day=8),
                'categoria': categorias['Moradia'],
                'pessoa': pessoas['Imobiliária Horizonte'],
                'forma_pagamento': boleto,
                'valor': Decimal('1800.00'),
                'parcelas': 1,
                'pagamentos': {},
            },
            {
                'descricao': 'Conta de energia',
                'tipo': 'despesa',
                'data': hoje.replace(day=18),
                'categoria': categorias['Contas da casa'],
                'pessoa': pessoas['Companhia de Energia'],
                'forma_pagamento': boleto,
                'valor': Decimal('230.40'),
                'parcelas': 1,
                'pagamentos': {},
            },
            {
                'descricao': 'Internet e telefone',
                'tipo': 'despesa',
                'data': hoje.replace(day=28),
                'categoria': categorias['Contas da casa'],
                'pessoa': pessoas['Operadora Conecta'],
                'forma_pagamento': boleto,
                'valor': Decimal('149.90'),
                'parcelas': 1,
                'pagamentos': {},
            },
            {
                'descricao': 'Compras do mercado',
                'tipo': 'despesa',
                'data': hoje - timedelta(days=2),
                'categoria': categorias['Alimentação'],
                'pessoa': pessoas['Mercado Central'],
                'forma_pagamento': pix,
                'valor': Decimal('500.00'),
                'desconto': Decimal('13.27'),
                'parcelas': 1,
                'pagamentos': {1: hoje - timedelta(days=2)},
            },
            {
                'descricao': 'Mercado do mês passado',
                'tipo': 'despesa',
                'data': deslocar_meses(hoje.replace(day=12), -1),
                'categoria': categorias['Alimentação'],
                'pessoa': pessoas['Mercado Central'],
                'forma_pagamento': pix,
                'valor': Decimal('612.35'),
                'parcelas': 1,
                'pagamentos': {1: deslocar_meses(hoje.replace(day=12), -1)},
            },
            {
                'descricao': 'Notebook parcelado',
                'tipo': 'despesa',
                'data': hoje - timedelta(days=65),
                'categoria': categorias['Lazer'],
                'pessoa': pessoas['Loja Tech'],
                'forma_pagamento': credito,
                'valor': Decimal('3600.00'),
                'parcelas': 6,
                'intervalo_parcelas': 30,
                'pagamentos': {
                    1: hoje - timedelta(days=65),
                    2: hoje - timedelta(days=35),
                },
                'troca_forma': {2: pix},
            },
            {
                'descricao': 'Mensalidade da academia',
                'tipo': 'despesa',
                'data': hoje.replace(day=2),
                'categoria': categorias['Saúde'],
                'pessoa': pessoas['Academia Movimento'],
                'forma_pagamento': credito,
                'valor': Decimal('360.00'),
                'parcelas': 3,
                'intervalo_parcelas': 30,
                'pagamentos': {1: hoje.replace(day=2)},
            },
        ]
