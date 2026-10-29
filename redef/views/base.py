from django.views import View
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin


from redef.helper import LoginHelper

class Perms:

    can_view_servidor = 'webmailufc.can_view_servidor'
    can_change_servidor = 'webmailufc.can_change_servidor'
    can_add_servidor = 'webmailufc.can_add_servidor'
    
    can_view_discente = 'webmailufc.can_view_discente'
    can_change_discente = 'webmailufc.can_change_discente'
    can_add_discente = 'webmailufc.can_add_discente'

class BaseView(LoginRequiredMixin,View):

    def __init__(self):
        self.login_helper = LoginHelper()

    DISCENTE = 'discente'
    SERVIDOR = 'servidor'

    TIPOS_CONTA = {
        DISCENTE: '@alu.ufc.br',
        SERVIDOR: '@ufc.br'
    }

    # has_vinculo_servidor
    @property
    def has_servidor_perm(self):
        return self.request.user.has_perm(Perms.can_view_servidor)

    # has_vinculo_dicente
    @property
    def has_discente_perm(self):
        return self.request.user.has_perm(Perms.can_view_discente)
    
    @property
    def is_servidor(self):
        return len(self.request.user.groups.filter(name='Servidores')) > 0

    @property
    def is_servidor_ativo(self):
        return self.request.session.get('is_discente_ativo',False)
    
    @property
    def is_discente_ativo(self):
        return self.request.session.get('is_servidor_ativo',False)
    
    @property
    def is_discente(self):
        return len(self.request.user.groups.filter(name='Alunos')) > 0

    @property
    def siape_servidor(self):
        _ =  self.login_helper.get_servidor({'pessoa__cpf':self.request.user.usuario_pessoa.cpf}, return_object=True)
        if _:
            return _.siape
        else:
            return None
    
    @property
    def matricula_discente(self):
        q = None
        if not self.request.user.usuario_pessoa.cpf:
            q = {'pessoa__pessoa_usuario__login__iexact':self.request.user.username}
        else:
            q = {'pessoa__cpf':self.request.user.usuario_pessoa.cpf}

        _ = self.login_helper.get_discente(q)
        if _:
            try:
                nivel_disc = _.filter(nivel__in=self.login_helper.NIVEL_DISCENTE) or _
                nivel_disc = nivel_disc.filter(status__in=self.login_helper.IDS_DISCENTE_STATUS_ATIVO).first() or nivel_disc.first()
                return nivel_disc.matricula
            except:
                ''
        else:
            return ''

    def get_contas(self, setorial=False, tipo_atual=False,servidor=False, discente=False,suspenso=False):
        q = None
        if tipo_atual:
            q = Q(email__icontains=self.TIPOS_CONTA[self.request.GET.get('tipo')])
        elif servidor and not discente:
            q = ~Q(email__icontains=self.TIPOS_CONTA[self.DISCENTE])
        elif discente and not servidor:
            q = Q(email__icontains=self.TIPOS_CONTA[self.DISCENTE])
        
        if not q:
            q = Q()

        if setorial:
            q &= ( Q(setorial=True) | Q(setorial=False) )
        else:
            q &= Q(setorial=False)

        q &= Q(suspenso=suspenso)
        return self.request.user.usuario_pessoa.pessoa_contas.filter(q).all()
    
    def get_conta(self, email):
        try:
            return self.request.user.usuario_pessoa.pessoa_contas.get(email=email)
        except:
            return None