import hashlib
from .models import Servidor_SI3, Discente_SI3, Usuario_SI3, Pessoa
from parameters.models import Parametro
from webmailufc.exceptions import VinculoException, LoginException

from django.db import connection, connections
from django.db.models import Q

from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType

from webmailufc.models import User

from django.conf import settings

class LoginHelper:
   

    NIVEIS_NORMAIS = ['G','L','S','D']
    NIVEIS_EXTENSAO = ['X','R']

    
    def __init__(self):

        # parametros discente
        self.IDS_DISCENTE_STATUS_ATIVO = list(map(int,Parametro.objects.filter(nome='IDS_DISCENTE_STATUS_ATIVO').first().valor.split(',')))
        self.IDS_TIPO_DISCENTE = list(map(int,Parametro.objects.filter(nome='IDS_TIPO_DISCENTE').first().valor.split(',')))
        self.NIVEL_DISCENTE = Parametro.objects.filter(nome='NIVEL_DISCENTE').first().valor.split(',')
        self.IDS_SIT_DISC_EXCLUIDO = list(map(int,Parametro.objects.filter(nome='IDS_SIT_DISC_EXCLUIDO').first().valor.split(',')))

        # parametros servidor
        self.IDS_SERV_ATIVO = list(map(int,Parametro.objects.filter(nome='IDS_SERV_ATIVO').first().valor.split(','))) 
        self.IDS_SERVIDOR_SITUACAO_PERMITE_CRIAR = list(map(int,Parametro.objects.filter(nome='IDS_SERVIDOR_SITUACAO_PERMITE_CRIAR').first().valor.split(',')))
        self.IDS_SIT_SERV_HABILITADOS_LOGIN = list(map(int,Parametro.objects.filter(nome='IDS_SIT_SERV_HABILITADOS_LOGIN').first().valor.split(',')))    

    
    def is_cpf_valido(self, cpf):
        def _it(start,_,f):
            __ = 0
            for i in _[:f]:
                __ += int(i) * start
                start += 1
            return __
        f_dv = _it(1,cpf,-2) % 11
        s_dv = _it(0,cpf,-1) % 11
        f_dv = 0 if f_dv == 10 else f_dv
        s_dv = 0 if s_dv == 10 else s_dv
        return cpf[-2:] == str(f_dv)+str(s_dv)
    
    def get_si3_credential(self, login, senha):
        try:  
            _cpf = int(login)
            if len(login) != 11: raise Exception("Não atende quantidade mínima de caracteres")
            _cpf_str = str(_cpf).zfill(11)          
            is_valid = self.is_cpf_valido(_cpf_str)  

            if not is_valid:
                raise Exception('CPF Inválido')

            query = Q(pessoa__cpf=_cpf)
        except Exception as e:
            query = Q(pessoa__pessoa_usuario__login__iexact=login)
        
        usuario_si3 = Usuario_SI3.objects.using('comum').filter(query).first()
        if not usuario_si3:
            raise VinculoException()
        
        if settings.DEBUG:
            return usuario_si3

        if not self.password_check(usuario_si3.senha, senha):
            raise LoginException()
        else:
            return usuario_si3     

    def get_password_md5(self,password):
        return hashlib.md5(password.encode()).hexdigest() 
        
    def password_check(self, enc, password):
        return self.get_password_md5(password) == enc
    
    def get_vinculos_ativos(self,cpf):
        return self.get_servidor({'pessoa__cpf':cpf},inclui_aposentados=False),self.get_discente({'pessoa__cpf':cpf})

    def create_or_get_pessoa(self, dados):
        try:
            if not dados.get('cpf'):
                return Pessoa.objects.get(id_institucional=dados.get('id_institucional'))
            else:
                return Pessoa.objects.get(cpf=dados.get('cpf'))
        except Pessoa.DoesNotExist:
            pessoa = Pessoa(full_nome=dados.get('nome'),cpf=dados.get('cpf'),id_institucional=dados.get('id_institucional'),usuario=dados.get('user'))
            pessoa.save()
            return pessoa
    
    def create_or_update_user(self, dados, servidor, discente, user=None, update_username=None):
        
        if user and update_username and update_username != user.username:
            user.username = update_username
            user.save()

        if not user:
            user = User(username=dados.get('username'), first_name=dados.get('name'),email=dados.get('email'), is_staff=False, is_superuser=False, is_active=True)
            user.set_password(dados.get('password'))
            user.save()
        

        if servidor and not user.groups.filter(name='Servidores').exists():
            Group.objects.get(name='Servidores').user_set.add(user)
            user.user_permissions.add(Permission.objects.get(content_type = ContentType.objects.get_for_model(User),codename = 'can_view_servidor'))
            user.user_permissions.add(Permission.objects.get(content_type = ContentType.objects.get_for_model(User),codename = 'can_change_servidor'))

            if servidor.filter(Q(ativo__id_ativo__in=self.IDS_SERV_ATIVO) & Q(situacao__id_situacao__in=self.IDS_SERVIDOR_SITUACAO_PERMITE_CRIAR)).first():
                user.user_permissions.add(Permission.objects.get(content_type = ContentType.objects.get_for_model(User),codename = 'can_add_servidor'))
        
        if discente and not user.groups.filter(name='Alunos').exists():
            Group.objects.get(name='Alunos').user_set.add(user)
            user.user_permissions.add(Permission.objects.get(content_type = ContentType.objects.get_for_model(User),codename = 'can_view_discente'))
            user.user_permissions.add(Permission.objects.get(content_type = ContentType.objects.get_for_model(User),codename = 'can_change_discente'))

            if discente.filter(status__status__in=self.IDS_DISCENTE_STATUS_ATIVO).first():
                user.user_permissions.add(Permission.objects.get(content_type = ContentType.objects.get_for_model(User),codename = 'can_add_discente'))
        
        return user

    
    def get_discente(self, query, ativo_apenas=False, return_object=False):
        result_set = self.get_discente_by_fields(query).filter(~Q(status__in=self.IDS_SIT_DISC_EXCLUIDO) & Q(tipo__in=self.IDS_TIPO_DISCENTE) & Q(nivel__in=self.NIVEL_DISCENTE)).order_by('-ano_ingresso')

        if ativo_apenas:
            result_set = result_set.filter(status__in=self.IDS_DISCENTE_STATUS_ATIVO)
        
        if return_object:
            result_set = result_set.first()

        return result_set

    def get_discente_by_fields(self, query):
        query_object = Discente_SI3.objects.using('academico')
        if type(query) is Q:
            return query_object.filter(query)
        elif type(query).__name__ == 'dict':
            return query_object.filter(**query)
        else:
            return None
    
    def get_servidor(self, query, inclui_aposentados=False, return_object=False):
        situacao = Q(situacao__in=self.IDS_SERVIDOR_SITUACAO_PERMITE_CRIAR)
        ativo = Q(ativo__in=self.IDS_SERV_ATIVO)
        if inclui_aposentados:
            situacao |= Q(situacao__in=self.IDS_SIT_SERV_HABILITADOS_LOGIN)
            ativo |= Q(ativo__in=[2])

        
        result_set = self.get_servidor_by_fields(query).filter(situacao & ativo)

        if return_object:
            result_set = result_set.first()            

        return result_set

    def get_servidor_by_fields(self, query):
        query_object = Servidor_SI3.objects.using('administrativo')
        if type(query) is Q:
            return query_object.filter(query)
        elif type(query).__name__ == 'dict':
            return query_object.filter(**query)
        else:
            return None