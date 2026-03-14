from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Campus(models.Model):
    nome = models.CharField(max_length=60)
    atualizado_em = models.DateTimeField(auto_now=True)
    cadastrado_em = models.DateTimeField(auto_now_add=True)
    cadastrado_por = models.ForeignKey(User, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.nome}"
    
    
class Modalidade(models.Model):
    nome = models.CharField(max_length=60, help_text="Exemplo: LOL, CS, Fifa, etc.")

    def __str__(self):
        return f"{self.nome}"
    

class Etapa(models.Model):
    nome = models.CharField(max_length=60)
    quantidade_jogos = models.PositiveSmallIntegerField(
        verbose_name="quantidade de jogos",
        help_text="Informe quantos jogos tem nesta etapa, ex: Quartas de final tem 4 jogos."
    )

    def __str__(self):
        return f"{self.nome} ({self.quantidade_jogos})"
    

class Jogador(models.Model):
    nome = models.CharField(max_length=60)
    id_jogador = models.CharField(max_length=100, verbose_name="ID do jogador", help_text="Informe o id do jogador, ex: nome#1234")
    campus = models.ForeignKey(Campus, on_delete=models.PROTECT)
    atualizado_em = models.DateTimeField(auto_now=True)
    cadastrado_em = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.nome} ({self.id_jogador})"
    

class Campeonato(models.Model):
    nome = models.CharField(max_length=100)
    campus = models.ForeignKey(Campus, on_delete=models.PROTECT)
    data = models.DateField()
    data_inscricao = models.DateTimeField(verbose_name="data de inscrição", help_text="Informe a data limite para inscrição, ex: 2024-12-31")
    modalidades = models.ManyToManyField(Modalidade)
    atualizado_em = models.DateTimeField(auto_now=True)
    cadastrado_em = models.DateTimeField(auto_now_add=True)
    cadastrado_por = models.ForeignKey(User, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.nome} ({self.data})"
    

class Inscricao(models.Model):
    nome_time = models.CharField(max_length=60, verbose_name="Nome do time", help_text="Informe o nome do time, ex: Time Alpha")
    jogadores = models.ManyToManyField(Jogador)
    campeonato = models.ForeignKey(Campeonato, on_delete=models.PROTECT)
    modalidade = models.ForeignKey(Modalidade, on_delete=models.PROTECT)
    
    confirmada = models.BooleanField(default=False)
    confirmada_em = models.DateTimeField(null=True, blank=True)

    inscrito_em = models.DateTimeField(auto_now_add=True)
    inscrito_por = models.ForeignKey(User, on_delete=models.PROTECT)

    def __str__(self):
        if self.confirmada:
            return f"{self.nome_time} - {self.campeonato} [✅]"
        else:
            return f"{self.nome_time} - {self.campeonato} [❌]"
    
    
class Jogo(models.Model):
    time_1 = models.ForeignKey(Inscricao, on_delete=models.PROTECT, related_name="time_1")
    time_2 = models.ForeignKey(Inscricao, on_delete=models.PROTECT, related_name="time_2")
    data_hora = models.DateTimeField(null=True, blank=True, verbose_name="data e hora do jogo", help_text="Informe a data e hora do jogo, ex: 2024-12-31 18:00")
    etapa = models.ForeignKey(Etapa, on_delete=models.PROTECT)
    modalidade = models.ForeignKey(Modalidade, on_delete=models.PROTECT)
    
    resultado = models.CharField(max_length=30, null=True, blank=True, verbose_name="resultado do jogo", help_text="Informe o resultado do jogo, ex: 2-1")
    vencedor = models.ForeignKey(Inscricao, on_delete=models.PROTECT, null=True, blank=True, related_name="vencedor")

    atualizado_em = models.DateTimeField(auto_now=True)
    cadastrado_em = models.DateTimeField(auto_now_add=True)
    cadastrado_por = models.ForeignKey(User, on_delete=models.PROTECT)

    def __str__(self):
        return f"Jogo #{self.pk} às {self.data_hora}"