from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from redef.helper import LoginHelper
from webmailufc.gsuiteaccess import Google
from .base import BaseView


class RedefineView(BaseView):
    template_name = "redefine.html"

    contas = None

    def __init__(self):
        super().__init__()
        self.login_helper = LoginHelper()

    @method_decorator(login_required)    
    def dispatch(self, request, *args, **kwargs):
        tipo = request.GET.get('tipo')

        if not tipo or tipo.lower() not in ['all','servidor','discente']:
            return HttpResponseRedirect(reverse('redef:login'))
        
        tipo = tipo.lower()

        if tipo == 'all':
            self.contas = self.get_contas(setorial=True)
        else:
            self.contas = self.get_contas(tipo_atual=True,setorial=True)
        if not tipo or len(self.contas) == 0:
            return HttpResponseRedirect(reverse('redef:login'))
        return super().dispatch(request, *args, **kwargs)    

    def get(self,request):
        contas = []
        for conta in self.contas:
            auxconta = { 'email': conta.email }
            contas.append(auxconta)
            if not conta.email_alternativo or not conta.nome or conta.sobrenome:
                google = Google(Google.get_credentials(conta.email))
                email_google = google.exists(conta.email)
                if not email_google:
                    continue
                auxconta['email_alternativo'] = email_google.get('recoveryEmail')
                auxconta['telefone'] = email_google.get('recoveryPhone')
                if email_google.get('name'):
                    auxconta['nome'] = email_google['name'].get('givenName')
                    auxconta['sobrenome'] = email_google['name'].get('familyName')
            else:
                auxconta['email_alternativo'] = conta.email_alternativo
                auxconta['nome'] = conta.nome
                auxconta['sobrenome'] = conta.sobrenome

        
        return render(request,self.template_name,{
            'has_outros_vinculos': (self.is_servidor_ativo and self.is_discente_ativo) or request.session.get('user_has_other_accs',False),
            'has_outros_emails': (not self.is_discente and self.is_servidor) and self.get_contas(servidor=True),
            'contas': contas
        })