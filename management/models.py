from django.db import models


class Medium(models.Model):
    ROLE_CHOICES = [
        ('MEMBRO', 'Membro'),
        ('CAMBONE', 'Cambone'),
        ('COORDENADOR', 'Coordenador'),
        ('DIRECAO', 'Direção'),
        ('ADMINISTRATIVO', 'Administrativo'),
        ('OUTRO', 'Outro'),
    ]

    nome_completo = models.CharField(max_length=200)
    nome_religioso = models.CharField(max_length=100, blank=True)
    data_nascimento = models.DateField()
    data_entrada = models.DateField(auto_now_add=True)
    telefone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    ativo = models.BooleanField(default=True)
    papel = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='MEMBRO',
        help_text='Função do colaborador dentro do centro'
    )
    cargo = models.CharField(
        max_length=100,
        blank=True,
        help_text='Cargo ou função específica dentro do papel'
    )

    def __str__(self):
        if self.cargo:
            return f"{self.nome_completo} ({self.cargo})"
        return self.nome_completo


class Evento(models.Model):
    TIPO_CHOICES = [
        ('GIRA', 'Gira'),
        ('FESTA', 'Festa'),
        ('TRABALHO', 'Trabalho Especial'),
        ('REUNIAO', 'Reunião'),
    ]

    titulo = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    data = models.DateField()
    horario = models.TimeField()
    descricao = models.TextField(blank=True)

    def __str__(self):
        return f"{self.titulo} - {self.data}"


class Presenca(models.Model):
    medium = models.ForeignKey(Medium, on_delete=models.CASCADE)
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE)
    presente = models.BooleanField(default=False)
    data_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('medium', 'evento')


class Tarefa(models.Model):
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('EM_ANDAMENTO', 'Em andamento'),
        ('CONCLUIDA', 'Concluída'),
    ]

    medium = models.ForeignKey(
        Medium,
        on_delete=models.CASCADE,
        related_name='tarefas'
    )
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_vencimento = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDENTE'
    )

    def __str__(self):
        return f"{self.titulo} - {self.medium.nome_completo}"


class Financeiro(models.Model):
    TIPO_MOVIMENTACAO = [
        ('ENTRADA', 'Entrada (Doação/Mensalidade)'),
        ('SAIDA', 'Saída (Despesa)'),
    ]

    descricao = models.CharField(max_length=200)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    tipo = models.CharField(max_length=10, choices=TIPO_MOVIMENTACAO)
    data = models.DateField(auto_now_add=True)
    medium = models.ForeignKey(
        Medium, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.tipo}: {self.descricao} - R$ {self.valor}"


class Banho(models.Model):
    TIPO_BANHO = [
        ('LIMPEZA', 'Banho de Limpeza'),
        ('PODER', 'Banho de Poder'),
        ('PROTECAO', 'Banho de Proteção'),
        ('SAUDE', 'Banho de Saúde'),
        ('OUTRO', 'Outro'),
    ]

    titulo = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_BANHO)
    data = models.DateField()
    horario = models.TimeField(null=True, blank=True)
    medium = models.ForeignKey(
        Medium, on_delete=models.SET_NULL, null=True, blank=True,
        help_text='Responsável ou atendente do banho')
    descricao = models.TextField(blank=True)
    data_registro = models.DateTimeField(auto_now_add=True)
    entidade = models.CharField(
        max_length=100, blank=True, help_text='Entidade associada ao banho')

    def __str__(self):
        return f"{self.titulo} - {self.get_tipo_display()}"


class Material(models.Model):
    nome = models.CharField(max_length=100)
    categoria = models.CharField(max_length=50, blank=True)
    quantidade_atual = models.IntegerField(default=0)
    quantidade_minima = models.IntegerField(
        default=5, help_text="Aviso quando o estoque estiver abaixo disso")
    unidade_medida = models.CharField(max_length=20, default='unidade')

    def __str__(self):
        return f"{self.nome} ({self.quantidade_atual} {self.unidade_medida})"


class MovimentacaoEstoque(models.Model):
    TIPO_MOV = [
        ('ENTRADA', 'Entrada (Compra/Doação)'),
        ('SAIDA', 'Saída (Uso/Perda)'),
    ]

    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    quantidade = models.IntegerField()
    tipo = models.CharField(max_length=10, choices=TIPO_MOV)
    data = models.DateTimeField(auto_now_add=True)
    observacao = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if self.tipo == 'ENTRADA':
            self.material.quantidade_atual += self.quantidade
        else:
            self.material.quantidade_atual -= self.quantidade
        self.material.save()
        super().save(*args, **kwargs)
