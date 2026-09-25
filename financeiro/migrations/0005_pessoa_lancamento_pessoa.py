from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def apagar_lancamentos_existentes(apps, schema_editor):
    Lancamento = apps.get_model('financeiro', 'Lancamento')
    Lancamento.objects.using(schema_editor.connection.alias).all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('financeiro', '0004_ordenacao_modelos'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Pessoa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=150, verbose_name='Nome')),
                ('documento', models.CharField(max_length=18, unique=True, verbose_name='CPF ou CNPJ')),
                ('cep', models.CharField(max_length=9, verbose_name='CEP')),
                ('endereco', models.CharField(max_length=255, verbose_name='Endereço')),
                ('cidade', models.CharField(max_length=100, verbose_name='Cidade')),
                ('status', models.BooleanField(default=True, verbose_name='Ativo')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('criado_por', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Pessoa',
                'verbose_name_plural': 'Pessoas',
                'ordering': ['nome'],
            },
        ),
        migrations.RunPython(apagar_lancamentos_existentes, migrations.RunPython.noop),
        migrations.AddField(
            model_name='lancamento',
            name='pessoa',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='financeiro.pessoa', verbose_name='Cliente/Fornecedor'),
        ),
    ]