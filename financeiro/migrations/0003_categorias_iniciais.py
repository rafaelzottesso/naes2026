from django.db import migrations


CATEGORIAS = [
    ("Salário", "Remuneração do trabalho, pró-labore ou aposentadoria."),
    ("Renda extra", "Freelas, comissões, bicos e vendas eventuais."),
    ("Rendimentos", "Juros, dividendos e outros ganhos de investimentos."),
    ("Moradia", "Aluguel, financiamento, condomínio, IPTU e manutenção da casa."),
    ("Contas da casa", "Água, energia, gás, internet e telefone."),
    ("Alimentação", "Supermercado, feira, padaria, restaurante e delivery."),
    ("Transporte", "Combustível, transporte público, aplicativos e manutenção do veículo."),
    ("Saúde", "Plano de saúde, consultas, exames e farmácia."),
    ("Educação", "Mensalidades, cursos e material."),
    ("Lazer", "Passeios, viagens, cinema e entretenimento."),
    ("Vestuário e cuidados pessoais", "Roupas, calçados, higiene e beleza."),
    ("Dívidas e empréstimos", "Parcelas de empréstimo, cartão e acordos."),
    ("Impostos e taxas", "Impostos, contribuições e tarifas bancárias."),
    ("Assinaturas", "Streaming, aplicativos e outros serviços recorrentes."),
]


def criar_categorias(apps, schema_editor):
    Categoria = apps.get_model("financeiro", "Categoria")
    User = apps.get_model("auth", "User")
    usuario = User.objects.filter(is_superuser=True).order_by("id").first()
    if usuario is None:
        usuario = User.objects.order_by("id").first()
    if usuario is None:
        return

    for nome, descricao in CATEGORIAS:
        Categoria.objects.get_or_create(
            nome=nome,
            defaults={
                "descricao": descricao,
                "status": True,
                "criado_por": usuario,
            },
        )


def remover_categorias(apps, schema_editor):
    Categoria = apps.get_model("financeiro", "Categoria")
    Categoria.objects.filter(nome__in=[nome for nome, _ in CATEGORIAS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("financeiro", "0002_remove_categoria_tipo"),
    ]

    operations = [
        migrations.RunPython(criar_categorias, remover_categorias),
    ]
