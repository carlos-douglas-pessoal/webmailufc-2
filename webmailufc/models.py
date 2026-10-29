from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class Choices:
    ACAO_CHOICES = [
        (0, 'CRIACAO'),
        (1, 'ATUALIZAÇÃO DADOS PESSOAIS'),
        (2,'ATUALIZAÇÃO SENHA'),
        (3, 'SUSPENSÃO'),
        (4, 'EXCLUSÃO')        
    ]  

class User(AbstractUser):
    first_name = models.CharField(verbose_name='Primeiro Nome', max_length=200, blank=True)
    email = models.EmailField(verbose_name="Endereço de e-email",max_length=254, blank=True, null=True)
    
    def get_nome(self):
        return self.first_name
    get_nome.short_description = "Nome completo"
    
    class Meta:
        permissions = [
            ("can_add_discente","Usuário pode criar contas @alu.ufc.br"),
            ("can_change_discente","Usuário pode redefinir contas @alu.ufc.br"),
            ("can_view_discente","Usuário pode ver contas @alu.ufc.br"),
            
            ("can_add_servidor","Usuário pode criar contas @ufc.br"),
            ("can_change_servidor","Usuário pode redefinir contas @ufc.br"),
            ("can_view_servidor","Usuario pode ver contas @ufc.br")
            
        ]
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

class LogEntrada(models.Model):
    id = models.AutoField(primary_key=True)
    pessoa = models.ForeignKey('redef.Pessoa', related_name='registros_entrada', on_delete=models.CASCADE, null=False,verbose_name='Pessoa')
    data_e = models.DateTimeField(default=timezone.now,blank=False,verbose_name='Data de Entrada')
    data_s = models.DateTimeField(null=True,blank=False,verbose_name='Data de Saída')
    ip = models.TextField(null=False, blank=False,verbose_name='IP')
    nat = models.TextField(null=False, blank=False,verbose_name='NAT')
    user_agent = models.TextField(null=False, blank=False,verbose_name='Browser')

    def get_login(self):
        return self.pessoa.usuario.username
    get_login.short_description = 'Login'

    def get_data_e(self):
        return self.data_e.strftime('%d/%m/%Y %H:%M')
    get_data_e.short_description = "Data de Entrada"

    def get_data_s(self):
        return self.data_s.strftime('%d/%m/%Y %H:%M') if self.data_s else '-' 

    def __str__(self):
        entrada = self.data_e.strftime('%d/%m/%Y %H:%Mh')
        saida = self.data_s and self.data_s.strftime('%d/%m/%Y %H:%Mh')
        return f"{self.pessoa.full_nome} [ Entrada às {entrada} ] [ Saída às {saida} ]"

    class Meta:
        managed = True
        db_table = 'log_entrada'
        verbose_name = "Log Entrada (Usuário)"
        verbose_name_plural = "Log Entradas (Usuários)"

import pytz
class LogAcao(models.Model):    
    id = models.AutoField(primary_key=True)
    acao = models.SmallIntegerField(choices=Choices.ACAO_CHOICES,verbose_name='Ação')
    conta = models.ForeignKey('redef.Conta',related_name='log_conta',on_delete=models.DO_NOTHING, null=False)
    data_acao = models.DateTimeField(default=timezone.now,verbose_name='Data da ação')

    CRIACAO = 0
    ATUALIZACAO = 1
    SUSPENSAO = 2
    EXCLUSAO = 3

    CRIACAO_EMAIL = 0
    ALTERACAO_DADOS = 1
    ALTERACAO_SENHA = 2
    ALTEROU_FOTO = 3

    def get_data_acao(self):
        return self.data_acao.strftime('%d/%m/%Y %H:%M')
    get_data_acao.short_description = 'Data'

    def get_login(self):
        return self.conta.pessoa.usuario.username
    get_login.short_description = 'Login'

    def get_pessoa_acao(self):
        return self.conta.pessoa.full_nome
    get_pessoa_acao.short_description = 'Proprietário'

    class Meta:
        managed = True
        db_table = 'log_acao'
        verbose_name = "Log Ação (Usuário)"
        verbose_name_plural = "Log Ações (Usuários)"

    def __str__(self):
        return f'{self.conta} - {self.get_acao_display()} em {self.data_acao.strftime("%d/%m/%Y às %H:%Mh")}'

class ImportacaoContas(models.Model):
    id = models.AutoField(primary_key=True)
    csv = models.FileField(verbose_name='CSV',upload_to='files/csv/')
    data_cadastro = models.DateTimeField(default=timezone.now)
    cadastrado_por = models.ForeignKey(User,related_name='arquivos_csv',null=False,on_delete=models.DO_NOTHING)
    processado = models.BooleanField(help_text="Indica se o arquivo foi processado",default=False)
    
    def get_nome_arquivo(self):
        return self.csv.name[self.csv.name.rfind('/')+1:]
    get_nome_arquivo.short_description = "Nome do Arquivo"

    def __str__(self):
        return f'Arquivo de {self.data_cadastro}'

    class Meta:
        managed = True
        db_table = 'importacao_contas_csv'    
        verbose_name = "Arquivo de Contas"
        verbose_name_plural = "Importação de Contas (CSV)"

class CriticaImportacaoContas(models.Model):
    id = models.AutoField(primary_key=True)
    linha = models.TextField()
    arquivo = models.ForeignKey(ImportacaoContas,on_delete=models.CASCADE,related_name='criticas')

    class Meta:
        managed = True
        db_table = 'critica_importacao_contas'
        verbose_name = "Crítica Importação"
        verbose_name_plural = "Crítica Importação Contas"

class CadastroEmail(models.Model):
    id = models.AutoField(primary_key=True)
    cpf = models.CharField(max_length=500)
    email_ufc = models.CharField(max_length=500)
    data_cadastro = models.DateTimeField(max_length=500)
    setorial = models.BooleanField()
    email_alternativo = models.CharField(max_length=500)
    nome_config = models.CharField(max_length=500)
    sobrenome_config = models.CharField(max_length=500)
    siape = models.CharField(max_length=500)
    suspenso = models.BooleanField()
    status = models.CharField(max_length=500)

    class Meta:
        managed = False
        db_table = 'cadastro_email'