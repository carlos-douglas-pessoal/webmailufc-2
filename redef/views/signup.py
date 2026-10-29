from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.db.models import Q
from django.conf import settings
from datetime import datetime
import logging

from ..models import Conta
from ..forms import SignUpForm, UserSignUpForm
from ..helper import LoginHelper
from webmailufc.models import LogAcao
from webmailufc.exceptions import FormularioCadastroException, UsuarioJaExisteException, VinculoException
from webmailufc.gsuiteaccess import Google
from .base import BaseView


class SignUpView(BaseView):
    template_name = "signup.html"
    

    siape = None    
    alias = None
    obj = None
    has_discente = None
    has_servidor = None 
    has_outros_vinculos = None
    logger = logging.getLogger('django')

    @method_decorator(login_required)     
    def dispatch(self, request, *args, **kwargs):
        tipo = request.GET.get('tipo')
        if not tipo or (tipo.lower() not in ['discente','servidor']):
            return HttpResponseRedirect(reverse('redef:vinculos'))
        
        tipo = tipo.lower()

        self.has_discente = self.get_contas(discente=True)
        self.has_servidor = self.get_contas(servidor=True)

        # if (self.is_servidor and self.has_servidor and tipo == 'servidor') or (self.is_discente and self.has_discente and tipo == 'discente'):
        #     return HttpResponseRedirect(reverse('redef:redefinir') + f'?tipo={tipo}')
        # elif (tipo == 'servidor' and not self.is_servidor) or (tipo == 'discente' and not self.is_discente):
        #     return HttpResponseRedirect(reverse('redef:login'))
            

        self.alias = self.TIPOS_CONTA[tipo]
        self.obj = {'alias':self.alias,'has_outros_vinculos':self.is_discente_ativo and self.is_servidor_ativo,'siape':self.siape_servidor,'matricula':self.matricula_discente}
        return super().dispatch(request, *args, **kwargs) 
    
    def get(self,request):
        self.obj['teste'] = UserSignUpForm()        
        if request.GET.get('tipo') == 'servidor':            
            self.obj['show_message'] = self.has_discente and ((request.session.get('is_discente_ativo') or False) ^ (request.session.get('is_servidor_ativo') or False))
            if self.obj['show_message']:
                request.session['user_has_other_accs'] = True

        return render(request,self.template_name,self.obj)

    def post(self,request):
        # verifica se tem o vínculo e se existe conta```
        form = SignUpForm(request.POST)
        try:        
            if form.is_valid() and form.cleaned_data.get('vinculo') and form.cleaned_data.get('vinculo') in ['discente','servidor']: 
                if (form.cleaned_data.get('vinculo') == 'discente' and not self.is_discente) or (form.cleaned_data.get('vinculo') == 'servidor' and not self.is_servidor):
                    raise Exception("Usuário não possui este vínculo: " + form.cleaned_data.get('vinculo'))
                _lhelper = LoginHelper()
                ## validação extra
                q = {}
                if not request.user.usuario_pessoa.cpf:
                    {'pessoa__pessoa_usuario__login__iexact':request.user.username}
                else:
                    q = {'pessoa__cpf': request.user.usuario_pessoa.cpf}
                if(form.cleaned_data.get('vinculo') == 'discente'):                    
                    discente_si3 = _lhelper.get_discente(q,ativo_apenas=True)
                    if discente_si3 is None:
                        raise VinculoException(message="Você não possui matrícula ativa com a instituição")
                elif (form.cleaned_data.get('vinculo') == 'servidor'):                    
                    servidor_si3 = _lhelper.get_servidor(q,inclui_aposentados=False)
                    if servidor_si3 is None:
                        raise VinculoException(message="Você não possui um vínculo ativo com a instituição")
                ## fim validação extra
                return self.sucesso(form)
            else:
                raise FormularioCadastroException()
        except Exception as E:
            if E.__class__.__name__ in ['UsuarioJaExisteException','VinculoException','FormularioCadastroException']:
                self.obj["erro"] = str(E)
            else:
                erro_justificativa = None
                if 'Invalid recovery phone' in str(E):
                    erro_justificativa = 'Formato do telefone está inválido.'
                self.obj["erro"] = "Ocorreu um erro ao tentar criar uma conta.Por favor,revise os campos e tente novamente."
                if erro_justificativa:
                    self.obj["erro"] += erro_justificativa
                self.logger.error(f"\n[{request.user.username}] [{datetime.now()}] Erro ao criar conta\n>> {str(E)}")
            return render(request,self.template_name,self.obj)

    def sucesso(self,form):
        google_instance = None
        if form.cleaned_data.get('vinculo') == self.SERVIDOR:
            google_instance = Google(Google.SERV_CREDENTIALS)
        elif form.cleaned_data.get('vinculo') == self.DISCENTE:
            google_instance = Google(Google.ALU_CREDENTIALS)
        else:
            raise Exception("Tipo de vínculo inválido")

        primary_email = f"{form.cleaned_data['nome_usuario']}{self.TIPOS_CONTA[form.cleaned_data.get('vinculo')]}"

        if google_instance.exists(primary_email):
            raise UsuarioJaExisteException(primary_email)
        
        data_ = form.cleaned_data
        insert_user = None  

        conta = Conta(nome=data_['nome'],sobrenome=data_['sobrenome'],email=primary_email,
                        email_alternativo=data_['email_alternativo'],setorial=False,suspenso=False,pessoa=self.request.user.usuario_pessoa)
        
        if not settings.DEBUG:            
            insert_user, pwd = google_instance.insert(primary_email,conta.nome,conta.sobrenome,conta.email_alternativo,data_['telefone'])
        else:
            pwd = 'senha_debug_mode'
            # insert_user = {}

        if insert_user is not None and pwd and not settings.DEBUG:
            # conta.save() 
            raise Exception("testes " + str(insert_user))             
            # LogAcao(acao=LogAcao.CRIACAO,conta=conta).save()

        self.request.session['credentials'] = {'user':primary_email,'password':pwd}                 
                
        return HttpResponseRedirect(reverse('redef:sucesso'))