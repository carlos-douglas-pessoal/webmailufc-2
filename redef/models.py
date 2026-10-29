from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.db.models import Q

# SI3


class Unidade(models.Model):
    id_unidade = models.IntegerField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'comum"."unidade'

class InstituicaoEnsino(models.Model):
    id = models.IntegerField(primary_key=True)
    nome = models.CharField(max_length=150)
    sigla = models.CharField(max_length=20)
    estrangeira = models.BooleanField()

    def __str__(self):
        return self.nome

    class Meta:
        managed = False
        db_table = 'comum"."instituicoes_ensino'


class Ativo(models.Model):
    id_ativo = models.IntegerField(primary_key=True)
    descricao = models.TextField()
    permite_acesso_sist_rh = models.BooleanField()

    def __str__(self):
        return self.descricao

    class Meta:
        managed = False
        db_table = 'rh"."ativo'

class SituacaoServidor(models.Model):
    id_situacao = models.IntegerField(primary_key=True)
    descricao = models.TextField()

    def __str__(self):
        return self.descricao

    class Meta:
        managed = False
        db_table = 'rh"."situacao_servidor'

class StatusDiscente(models.Model):
    status = models.IntegerField(primary_key=True)
    descricao = models.TextField()
    situacao_vinculo = models.TextField()

    def __str__(self):
        return self.descricao

    class Meta:
        managed = False
        db_table = 'public"."status_discente'


class Pessoa_SI3(models.Model):
    id_pessoa = models.IntegerField(primary_key=True)
    nome = models.TextField()
    cpf = models.BigIntegerField(db_column='cpf_cnpj')
    email = models.TextField() 
    id_institucional = models.UUIDField(unique=True)

    def __str__(self):
        return self.nome

    class Meta:
        managed = False
        db_table = 'comum"."pessoa'

class Usuario_SI3(models.Model):
    id_usuario = models.IntegerField(primary_key=True)
    login = models.TextField()
    senha = models.TextField()
    pessoa = models.OneToOneField(Pessoa_SI3,db_column="id_pessoa",related_name='pessoa_usuario',on_delete=models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'comum"."usuario'

    def __str__(self):
        return self.login


# DiscenteGraduacao 
class Discente_SI3(models.Model):

    id_discente = models.IntegerField(primary_key=True)
    status = models.OneToOneField(StatusDiscente,on_delete=models.DO_NOTHING,db_column='status')
    matricula = models.IntegerField()
    ano_ingresso = models.IntegerField()
    nivel = models.CharField(max_length=1)
    tipo = models.SmallIntegerField()  
    pessoa = models.ForeignKey(Pessoa_SI3,db_column="id_pessoa",related_name='discente_pessoa',on_delete=models.DO_NOTHING)     

    def __str__(self):
        return f"{self.matricula} {self.pessoa.nome}"        


    class Meta:
        managed = False
        db_table = 'public"."discente'

class Servidor_SI3(models.Model):
    id_servidor = models.IntegerField(primary_key=True)
    siape = models.BigIntegerField()
    ativo = models.OneToOneField(Ativo,on_delete=models.DO_NOTHING,db_column='id_ativo')
    situacao = models.OneToOneField(SituacaoServidor,on_delete=models.DO_NOTHING,db_column='id_situacao')
    pessoa = models.ForeignKey(Pessoa_SI3,related_name='servidor_pessoa',db_column="id_pessoa",on_delete=models.DO_NOTHING)
    unidade = models.OneToOneField(Unidade,related_name='unidade_servidor',db_column="id_unidade",on_delete=models.DO_NOTHING)
    unidade_lotacao = models.OneToOneField(Unidade,db_column="id_unidade_lotacao",on_delete=models.DO_NOTHING)


    def __str__(self):
        return f'{self.siape} {self.pessoa.nome}'

    class Meta:
        managed = False
        db_table = 'rh"."servidor'


class DocenteExterno_SI3(models.Model):
    id_docente_externo = models.IntegerField(primary_key=True)
    matricula = models.CharField(max_length=6)
    prazo_validade = models.DateField()
    data_cadastro = models.DateField()
    data_fim = models.DateField()
    ativo = models.BooleanField()
    discente = models.OneToOneField(Discente_SI3,db_column="id_discente",related_name="docente_externo_discente",on_delete=models.DO_NOTHING)    
    unidade = models.OneToOneField(Unidade,db_column="id_unidade",related_name="docente_externo_unidade",on_delete=models.DO_NOTHING)
    servidor = models.OneToOneField(Servidor_SI3,db_column="id_servidor",related_name="docente_externo_servidor",on_delete=models.DO_NOTHING)
    pessoa = models.OneToOneField(Pessoa_SI3,db_column="id_pessoa",related_name="docente_externo_pessoa",on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.pessoa.full_nome

    class Meta:
        managed = False
        db_table = 'ensino"."docente_externo'

# ENDSI3

class Pessoa(models.Model):

    id = models.AutoField(primary_key=True)
    full_nome = models.TextField(blank=False, null=False,verbose_name='Nome Completo')    
    cpf = models.BigIntegerField(verbose_name='CPF',null=True)
    id_institucional = models.UUIDField(verbose_name='ID Institucional',editable=False, null=True)
    usuario = models.OneToOneField('webmailufc.User',related_name='usuario_pessoa',on_delete=models.DO_NOTHING,null=False)

    @property
    def cpf_text(self):
        if not self.cpf:
            return "SEM CPF"
        q = str(self.cpf).zfill(11)
        return f"{q[0:3]}.{q[3:6]}.{q[6:9]}-{q[9:11]}"
    
    def get_my_cpf(self):
        return self.cpf_text
    get_my_cpf.short_description = 'CPF'

    def get_my_name(self):
        return self.full_nome
    get_my_name.short_description = 'Nome Completo'

    def get_my_siape(self):
        try:
            from .helper import LoginHelper
            login_helper = LoginHelper()
            serv = login_helper.get_servidor({'pessoa__cpf':self.cpf},inclui_aposentados=True, return_object=True)
            if serv.ativo.id_ativo not in login_helper.IDS_SERVIDOR_SITUACAO_PERMITE_CRIAR:
                return mark_safe(f"<div style='color:red;font-weight:bold'>{serv.siape}</div>")
            else:
                return serv.siape
        except Exception as e:
            return '-'
    get_my_siape.short_description = 'Siape'


    def get_my_matricula(self):
        try:
            from .helper import LoginHelper
            login_helper = LoginHelper()
            q = {}
            if not self.cpf:
                q = {'pessoa__pessoa_usuario__login__iexact':self.request.user.username}
            else:
                q = {'pessoa__cpf':self.cpf}
            disc = login_helper.get_discente(q)
            if disc.filter(status__status__in=login_helper.IDS_DISCENTE_STATUS_ATIVO).first():
                return disc.filter(status__status__in=login_helper.IDS_DISCENTE_STATUS_ATIVO).first().matricula                
            else:
                return mark_safe(f"<div style='color:red;font-weight:bold'>{disc.first().matricula}</div>")
        except Exception as e:
            return '-'
    get_my_matricula.short_description = 'Matrícula SIGAA'


    
    class Meta:
        ordering = ['-full_nome']
        db_table = 'pessoa'

    def __str__(self):
        return f'{self.full_nome}'

class Conta(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.TextField(blank=False,null=True)
    sobrenome = models.TextField(blank=False, null=True)
    email = models.EmailField(unique=True, blank=False, null=False)
    email_alternativo = models.EmailField(blank=False,null=False)
    data_cadastro = models.DateTimeField(default=timezone.now)
    setorial = models.BooleanField(default=False, blank=False, null=False)
    suspenso = models.BooleanField(default=False)
    pessoa = models.ForeignKey(Pessoa, related_name='pessoa_contas', on_delete=models.DO_NOTHING, null=False)

    def get_my_data_cadastro(self):
        return self.data_cadastro.strftime('%d/%m/%Y %H:%M')
    get_my_data_cadastro.short_description = 'Data de cadastro'

    def get_my_setorial(self):
        return 'Sim' if self.setorial else 'Não'
    get_my_setorial.short_description = 'Setorial'

    def get_my_suspenso(self):
        return 'Sim' if self.suspenso else 'Não'
    get_my_suspenso.short_description = 'Suspenso'

    def get_my_pessoa(self):
        return self.pessoa.full_nome
    get_my_pessoa.short_description = 'Proprietário'

    def get_my_login(self):
        return self.pessoa.usuario.username
    get_my_login.short_description = 'Login'

    class Meta:
        managed = True
        ordering = ['-email']
        db_table = 'conta'

    def __str__(self):
        return self.email