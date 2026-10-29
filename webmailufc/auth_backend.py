from django.contrib.auth.backends import ModelBackend
from webmailufc.models import User
from django.contrib.auth.hashers import check_password
from redef.helper import *
from redef.models import *
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db.models import Q
from webmailufc.exceptions import VinculoException, LoginException

class AuthBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, token=None):
        login_helper = LoginHelper()
        has_usuario = None
        user = None

        if username is None or len(username) == 0:
            raise Exception("Usuário não pode estar vazio")
        if password is None or len(password) == 0:
            raise Exception("Senha não pode estar vazia")

        try:
            usuario_si3 = login_helper.get_si3_credential(username, password)
            pessoa = usuario_si3.pessoa
            if not pessoa:
                raise Exception("Login sem pessoa cadastrada.")
            try:
                user = User.objects.get(username__iexact=usuario_si3.login)
                if not check_password(password,user.password):
                    user.set_password(password)
                    user.save()
            except User.DoesNotExist:
                # verifica se pessoa trocou o login
                has_pessoa = Pessoa.objects.filter(Q(id_institucional=pessoa.id_institucional) | Q(cpf = pessoa.cpf)).first()  
                has_usuario = None   
                if has_pessoa:
                    if hasattr(has_pessoa,'usuario_pessoa'):
                        has_usuario = has_pessoa.usuario_pessoa
                
                user = has_usuario or None 

            q = {}
            if pessoa.cpf is not None:
                q = {'pessoa__cpf':pessoa.cpf}
            else:
                q = {'pessoa__pessoa_usuario__login__iexact':usuario_si3.login}


            servidor_si3_db = login_helper.get_servidor(q)
            discente_si3_db = login_helper.get_discente(q)            

            user = login_helper.create_or_update_user(
                {'username': usuario_si3.login,'name':pessoa.nome,'email':pessoa.email,'is_staff':False, 'is_superuser':False, 'is_active':True,'password': usuario_si3.senha},
                    servidor_si3_db,discente_si3_db, user, usuario_si3.login)                

            pessoa_db = login_helper.create_or_get_pessoa({'nome': pessoa.nome,'cpf': pessoa.cpf,'id_institucional': pessoa.id_institucional,'user': user})

            # usuário antigo sem login
            if (not hasattr(user,'usuario_pessoa')):
                if(pessoa_db.usuario is not None and pessoa_db.usuario.id != user.id):
                    pessoa_db.usuario = user
                    pessoa_db.save()

            return user
        except LoginException as ex:
            if token is None:
                return None
            raise LoginException()
        except VinculoException:
            if token is None:
                return None
            raise VinculoException()

    def get_user(self,user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
