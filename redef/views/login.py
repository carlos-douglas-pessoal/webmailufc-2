from django.views import View
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
import logging

from redef.models import Pessoa_SI3,Usuario_SI3,Discente_SI3,Servidor_SI3, Pessoa

from redef.helper import LoginHelper
from webmailufc.models import LogEntrada, LogAcao
from webmailufc.exceptions import VinculoException



def logout_(request):    
    if request.user.is_authenticated:
        try:
            ultimo_registro = request.user.usuario_pessoa.registros_entrada.filter(data_s=None).order_by('-data_e').first()
            result = timezone.now() - ultimo_registro.data_e
            if (result.total_seconds() <= 7200):
                ultimo_registro.data_s = timezone.now()
                ultimo_registro.save()
        except Exception as e:
            pass
        logout(request)
    return HttpResponseRedirect(reverse('redef:login'))


class LoginView(View):

    template_name = 'login.html'
    page_title = 'Login'
    logger = logging.getLogger('django')

    message_login_error = "Não foi possível conceder acesso se você se enquadra em alguma das opções:<br/>\
        <ul style='text-align:left'> \
            <li>• Discente com matrícula cancelada</li> \
            <li>• Discente em mobilidade (aluno especial)</li> \
            <li>• Discente sem vínculo ativo</li> \
            <li>• Docente Externo</li> \
            <li>• Servidor inativo</li> \
        </ul>"

    def get(self, request):
        erro = None
        try:
            if request.user.is_authenticated:
                is_valid = self.validate_user(request.user)                
                return is_valid
        except Exception as e:
            erro = str(e)            
        return render(request, self.template_name,{'erro':erro})

    def post(self, request):
        try:            
            user = authenticate(username=request.POST.get('login'), password=request.POST.get('senha'),token={})            
            validation = self.validate_user(user)
            if validation:
                login(request,user)
                LogEntrada(pessoa=user.usuario_pessoa,data_e=timezone.now(),ip=request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT'),nat=request.META.get('REMOTE_ADDR')).save()
                return validation 
            else:
                raise VinculoException(self.message_login_error)      
        except Exception as e:
            msg = ""
            if type(e).__name__ in ['LoginException','VinculoException']:
                msg = str(e)
            else:
                msg = f"Não foi possível acessar este sistema. " + str(e)
                self.logger.error(f"\n [{request.POST.get('login')}] [{datetime.now()}] Erro durante login\n {str(e)}")
            return render(request, self.template_name,{'erro':msg})
    
    def validate_user(self,user):
        login_helper = LoginHelper()
        url_redefine = None
        
        q = {}
            
        if not user.usuario_pessoa.cpf:
            q = {'pessoa__pessoa_usuario__login__iexact':user.username}
        else:
            q = {'pessoa__cpf':user.usuario_pessoa.cpf}

        discente = login_helper.get_discente(q,ativo_apenas=False)
        servidor = login_helper.get_servidor(q,inclui_aposentados=True)

        if not discente.all() and not servidor.all():
            raise VinculoException(self.message_login_error)


        discente_ativo = False
        servidor_ativo = False
        # if discente:
        #     discente_ativo = len(discente.filter(status__in=login_helper.IDS_DISCENTE_STATUS_ATIVO).all()) > 0
        #     if discente_ativo:
        #         self.request.session['is_discente_ativo'] = True
        if servidor:
            servidor_ativo = len(servidor.filter(ativo__in=login_helper.IDS_SERV_ATIVO,situacao__in=login_helper.IDS_SERVIDOR_SITUACAO_PERMITE_CRIAR).all()) > 0
            if servidor_ativo:
                self.request.session['is_servidor_ativo'] = True      

        if discente and servidor:
            if discente_ativo and servidor_ativo:
                return HttpResponseRedirect(reverse('redef:vinculos'))
        
        contas = user.usuario_pessoa.pessoa_contas.filter(~Q(email__icontains='@alu.ufc.br') & Q(suspenso=False) & Q(setorial=False)).all() or []
        contas_alu = user.usuario_pessoa.pessoa_contas.filter(email__icontains='@alu.ufc.br',suspenso=False).all() or []        
     
        if discente is not None:
            return HttpResponseRedirect(reverse('redef:cadastro') + '?tipo=discente')
            if True:
                # url_redefine = (reverse('redef:redefinir') + '?tipo=all') if len(contas) and len(contas_alu) > 0 else (reverse('redef:' + ('cadastro' if len(contas_alu) == 0 else 'redefinir')) + '?tipo=discente')
                # return HttpResponseRedirect(url_redefine)
                return HttpResponseRedirect(reverse('redef:cadastro') + '?tipo=discente')
            elif not discente_ativo and not servidor and len(contas_alu) > 0:
                # usuário tem email para redefinir, mas não é mais ativo
                url_redefine = reverse('redef:redefinir') + '?tipo=discente'
                return HttpResponseRedirect(url_redefine)        

        # if servidor is not None:
        #     if servidor_ativo:
        #         url_redefine = (reverse('redef:redefinir') + '?tipo=all') if len(contas) and len(contas_alu) > 0 else (reverse('redef:' + ('cadastro' if len(contas) == 0 else 'redefinir')) + '?tipo=servidor')                
        #         return HttpResponseRedirect(url_redefine)
        #     elif servidor.filter(situacao__in=[2]).count() > 0 and len(contas) > 0:
        #         # servidores aposentados podem logar, mas não podem criar
        #         tipo = '?tipo=all' if len(contas) > 0 and len(contas_alu) > 0 else '?tipo=servidor'
        #         url_redefine = reverse('redef:redefinir') + tipo
        #         return HttpResponseRedirect(url_redefine)
        
        return None