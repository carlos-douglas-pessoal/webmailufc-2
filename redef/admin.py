from django.contrib import admin
from django.contrib import messages
from django.contrib.admin.models import CHANGE
from django.contrib.admin.models import ADDITION

from django.utils.safestring import mark_safe
from django.conf import settings
from django.db.models import Q

from webmailufc.utils import enviar_senha
from webmailufc.logging import WebmailUFCLogging
from webmailufc.models import User
from webmailufc.gsuiteaccess import Google

from .models import Pessoa, Conta, Servidor_SI3, Discente_SI3
from .forms import PessoaForm, ContaForm

from webmailufc.admin_methods import AdminMethods, MyChangeList


@admin.register(Pessoa)
class PessoaAdmin(AdminMethods):
    form = PessoaForm

    obj = None  

    search_fields = ['full_nome__icontains','cpf']  
    list_display = ('get_my_cpf','get_my_name','get_my_siape','get_my_matricula')
    list_per_page = 10
    ordering = ('full_nome',)

    actions = ['listar_servidores','listar_discentes','listar_todos']
    search_placeholder = "nome, CPF, siape ou matrícula"

    def get_changelist(self, request, **kwargs):
        return MyChangeList
    
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        # extra_context['title'] = 'Lista de pessoas do SI3. Apenas para visualizar,não é possível editar'
        if object_id:
            extra_context['show_save'] = False
            extra_context['show_save_and_continue'] = False
            extra_context['show_save_and_add_another'] = False
            extra_context['show_delete_link'] = False
            extra_context['show_delete'] = False
        return super(PessoaAdmin, self).changeform_view(request, object_id, form_url, extra_context)    

    def has_delete_permission(self, request, obj = None):
        return False

    def has_add_permission(self, request):
        return True
    
    def has_change_permission(self, request, obj = None):
        return False

    def listar_servidores(self, request, queryset):
        super().message_user_(request,queryset)
    listar_servidores.short_description = "Lista de servidores cadastrados"

    def listar_discentes(self, request, queryset):
        super().message_user_(request,queryset)
    listar_discentes.short_description = "Lista de discentes cadastrados"

    def listar_todos(self, request, queryset):
        super().message_user_(request,queryset)
    listar_todos.short_description = "Listar todas as pessoas"

    def save_model(self, request, obj, form, change):
        super(PessoaAdmin, self).save_model(request, obj, form, change)
        self.obj = obj
    
    def message_user(self, request, message, level=messages.INFO, extra_tags='', fail_silently=False):
        if self.obj:
            messages.success(request,mark_safe(f"O registro de <a href='/admin/redef/conta/{self.obj.id}/change/'><strong>{self.obj}</strong></a> foi importado com sucesso!"))        
    
    def get_form(self, request, obj=None, **kwargs):
        return super(PessoaAdmin, self).get_form(request, obj, **kwargs)
    
    def changelist_view(self, request, extra_context=None):
        action = None
        queryset = None
        extra_context = {'title': 'Selecione uma pessoa para visualizar', 'search': 'Nome, CPF ou Siape'}
        if request.method == 'POST':
            try:
                action = self.get_actions(request)[request.POST['action']][0]
                if request.POST['action'] == 'listar_servidores':
                    queryset = self.model.objects.filter(usuario__groups__name='Servidores').values_list('id',flat=True).all()
                elif request.POST['action'] == 'listar_discentes':
                    queryset = self.model.objects.filter(usuario__groups__name='Alunos').values_list('id',flat=True)
                elif request.POST['action'] == 'listar_todos':
                    queryset = self.model.objects.values_list('id',flat=True).all()
                else:
                    queryset = self.model.objects.values_list('id',flat=True).all()
            except Exception as e:
                print(e)
            post = request.POST.copy()
            post.update({admin.helpers.ACTION_CHECKBOX_NAME: queryset})
            request._set_post(post)    
        return super(PessoaAdmin, self).changelist_view(request, extra_context)

@admin.register(Conta)
class ContaAdmin(AdminMethods):
    form = ContaForm

    actions = ['gerar_nova_senha','ativar_conta','suspender_conta','listar_emails_setoriais', 
    'listar_emails_suspensos','listar_conta_servidores','listar_conta_discente','listar_tudo']

    search_fields = ['email','email__contains','pessoa__cpf','pessoa__full_nome']
    list_display = ('email','email_alternativo','get_my_data_cadastro','get_my_setorial','get_my_suspenso','get_my_pessoa','get_my_login')
    list_per_page = 10
    ordering = ('email','data_cadastro',)

    search_placeholder = 'e-mail, nome, CPF, siape ou matrícula'

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if object_id:
            extra_context['show_save_and_add_another'] = False
            extra_context['show_delete_link'] = False
            extra_context['show_delete'] = False
        return super(ContaAdmin, self).changeform_view(request, object_id, form_url, extra_context)

    def get_changelist(self, request, **kwargs):
        return MyChangeList

    def save_model(self, request, obj, form, change):
        self.obj = obj
        create = False
        if not obj.id:
            create = True
        if not settings.DEBUG:
            super(ContaAdmin, self).save_model(request,obj,form,change)     
        if obj:
            pwd = None
            try:
                if not form.cleaned_data.get('apenas_salvar',False):
                    user,domain = obj.email.split('@')
                    google = Google(Google.get_credentials(obj.email))
                    # if 'alu' in domain:
                    #     google = Google(Google.ALU_CREDENTIALS)
                    # else:
                    #     google = Google(Google.SERV_CREDENTIALS)
                    if form.TypeForm == 'create':
                        if not settings.DEBUG:
                            user,pwd = google.insert(obj.email,obj.nome,obj.sobrenome,obj.email_alternativo,None)  
                            WebmailUFCLogging.log(request.user,self.conta_type, obj.id, str(obj), ADDITION, f"Conta {obj.email} criada")                       
                        try:
                            if not settings.DEBUG:
                                enviar_senha(obj.email,obj.email_alternativo,pwd,True,nome=obj.pessoa.full_nome)
                            self.is_email_sent = True                
                        except Exception as e2:
                            self.is_email_sent = False
                        if self.is_email_sent:
                            messages.success(request,mark_safe(f"A conta <strong><a href='/ufcadmin/redef/conta/{obj.id}/change/'>{obj.email}</a></strong> foi criada! Um e-mail contendo a senha foi enviado para o e-mail alternativo <strong>{obj.email_alternativo}<strong>."))
                        else:
                            messages.success(request,mark_safe(f"A conta <strong><a href='/ufcadmin/redef/conta/{obj.id}/change/'>{obj.email}</a></strong> foi criada! A senha é <strong>{pwd}</strong>"))
                    elif form.TypeForm == 'update':
                        if not settings.DEBUG:
                            google.update_personal_data(obj.email,{
                                'name': {
                                    'givenName': obj.nome,
                                    'familyName': obj.sobrenome
                                },
                                'recoveryEmail': obj.email_alternativo,
                                'suspended': obj.suspenso
                            })
                        messages.success(request,mark_safe(f"A conta <strong><a href='/ufcadmin/redef/conta/{obj.id}/change/'>{obj.email}</a></strong> foi atualizada!"))                                    
                else:
                    messages.success(request,mark_safe(f"A conta <strong><a href='/ufcadmin/redef/conta/{obj.id}/change/'>{obj.email}</a></strong> foi inserida no banco!"))
                self.success = True                
            except Exception as e1:
                if create:
                    try:
                        obj.delete()
                    except:
                        pass
                messages.error(request,mark_safe(f"Ocorreu um erro ao criar ou atualizar a conta <strong>{obj.email}</strong> <br/> {str(e1)}"))

    def message_user(self, request, message, level=messages.INFO, extra_tags='', fail_silently=False):
        pass  

    def get_form(self, request, obj=None, **kwargs):
        try:
            if obj and obj.pk:
                google = Google(Google.get_credentials(obj.email))
                _conta = google.exists(obj.email)
                update_obj = False
                if _conta:
                    if _conta.get('name'):
                        obj.nome = _conta['name'].get('givenName')
                        obj.sobrenome = _conta['name'].get('familyName')
                    if _conta.get('recoveryEmail'):
                        if _conta.get('recoveryEmail') != obj.email_alternativo: 
                            update_obj = True
                        obj.email_alternativo = _conta['recoveryEmail']
                    elif _conta.get('emails') and len(_conta['emails']) > 1:
                        if _conta['emails'][0]['address'] != obj.email_alternativo: 
                            update = True
                        obj.email_alternativo = _conta['emails'][0]['address']
                    if obj.suspenso != _conta.get('suspended'): 
                        update_obj = True
                    obj.suspenso = _conta.get('suspended')
                    if update_obj is True:
                        obj.save()
        except Exception as e:
            pass
        return super(ContaAdmin, self).get_form(request, obj, **kwargs) 
     

    # def get_form(self, request, obj=None, **kwargs):
    #     AdminForm = super(ContaAdmin, self).get_form(request, obj, **kwargs)
    #     class AdminFormWithRequest(AdminForm):
    #         def __new__(cls, *args, **kwargs):
    #             kwargs['request'] = request
    #             return AdminForm(*args, **kwargs)
    #     return AdminFormWithRequest

    def gerar_nova_senha(self, request, queryset):
        emails = []
        message = f'{self.conta_type.name.capitalize()} foi gerada nova senha'
        for conta in queryset:
            google = Google(Google.get_credentials(conta.email))
            pwd = google.create_password()
            email_alternativo = conta.email_alternativo
            if '|' in email_alternativo:
                email_alternativo = email_alternativo.split('|')[0].strip()
            elif not email_alternativo:
                conta_ = google.exists(conta.email)
                if conta_.get('recoveryEmail'):
                    email_alternativo = conta_.get('recoveryEmail')
                elif conta_.get('emails') and len(conta_.get('emails')) > 1:
                    email_alternativo = conta_.get('emails')[0]['address']
            emails.append(conta.email)
            if not settings.DEBUG and google.update_password(conta.email,pwd):
                if email_alternativo:
                    enviar_senha(conta.email,email_alternativo,pwd,False,nome=conta.pessoa.full_nome)                
                WebmailUFCLogging.log(request.user,self.conta_type, conta.id, str(conta), CHANGE, message)

        if len(emails) == 0:
            msg = "Não foi possível gerar uma senha para a(s) conta(s) selecionada(s)"
            messages.error(request,msg)
        else:
            emails = ','.join(emails)
            if not email_alternativo and len(queryset) == 1:
                msg = f"A conta <strong>{emails}</strong> não possui e-mail de recuperação. A nova senha gerada é <strong>{pwd}</strong>."
            else:
                msg = f"As senhas das contas <strong>{emails}</strong> foram atualizadas" if len(queryset) > 1 else f"A senha da conta <strong>{emails}</strong> foi atualizada. Um e-mail contendo a senha foi enviado para {email_alternativo}"
            messages.success(request,mark_safe(msg))
            
    gerar_nova_senha.short_description = "Gerar nova senha"

    def ativar_conta(self, request, queryset):
        emails = []
        message = f'{self.conta_type.name.capitalize()} foi ativada'
        for conta in queryset:
            google = Google(Google.get_credentials(conta.email))
            emails.append(conta.email)
            if not settings.DEBUG and google.suspend(conta.email,False):                
                WebmailUFCLogging.log(request.user,self.conta_type, conta.id, str(conta), CHANGE, message)
        if len(emails) == 0:
            msg = "Não foi possível ativar as contas selecionadas"
            messages.error(request,msg)
        else:
            emails = ','.join(emails)
            msg = f"A(s) conta(s) <strong>{emails}</strong> foi/foram ativada(s)"
            messages.success(request,mark_safe(msg))  
    ativar_conta.short_description = "Ativar conta"              
        
    def listar_emails_suspensos(self,request,queryset):
        super().message_user_(request, queryset)
    listar_emails_suspensos.short_description = "Listar e-mails que foram suspensos"

    def listar_emails_setoriais(self, request, queryset):
        super().message_user_(request, queryset)
    listar_emails_setoriais.short_description = "Listar e-mails setoriais da universidade"

    def listar_conta_servidores(self, request, queryset):
        super().message_user_(request, queryset)
    listar_conta_servidores.short_description = "Listar contas de servidores"

    def listar_conta_discente(self, request, queryset):
        super().message_user_(request, queryset)
    listar_conta_discente.short_description = "Listar contas de discentes"

    def listar_tudo(self, request, queryset):
        super().message_user_(request, queryset)
    listar_tudo.short_description = "Listar tudo"

    def suspender_conta(self, request, queryset):
        emails = []
        message = f'{self.conta_type.name.capitalize()} foi suspensa'
        for conta in queryset:
            google = Google(Google.get_credentials(conta.email))
            emails.append(conta.email)
            if not settings.DEBUG and google.suspend(conta.email,True):                
                WebmailUFCLogging.log(request.user,self.conta_type, conta.id, str(conta), CHANGE, message)
        if len(emails) == 0:
            msg = "Não foi possível suspender as contas selecionadas"
            messages.error(request,msg)
        else:
            emails = ','.join(emails)
            msg = f"A(s) conta(s) <strong>{emails}</strong> foi/foram suspensa(s)"
            messages.success(request,mark_safe(msg))
    suspender_conta.description = "Suspender conta"    

    def changelist_view(self, request, extra_context=None):
        action = None
        queryset = None
        extra_context = {'title': 'Selecione uma conta para visualizar', 'search_placeholder': 'Nome, e-mail, CPF ou Siape'}        
        if request.method == 'POST':
            try:
                action = self.get_actions(request)[request.POST['action']][0]
                if request.POST['action'] == 'listar_emails_suspensos':
                    queryset = self.model.objects.filter(suspenso=True).values_list('id',flat=True).all()
                elif request.POST['action'] == 'listar_emails_setoriais':
                    queryset = self.model.objects.filter(setorial=True).values_list('id',flat=True).all()
                elif request.POST['action'] == 'listar_conta_servidores':
                    queryset = self.model.objects.filter(~Q(email__icontains='@alu.ufc.br')).values_list('id',flat=True).all()
                elif request.POST['action'] == 'listar_conta_discente':
                    queryset = self.model.objects.filter(email__icontains='@alu.ufc.br').values_list('id',flat=True).all()
                elif request.POST['action'] == 'listar_tudo':
                    queryset = self.model.objects.all().values_list('id',flat=True).all()
                else:
                    queryset = self.model.objects.filter(id=request.POST[admin.helpers.ACTION_CHECKBOX_NAME]).values_list('id',flat=True)         
            except Exception as e:
                pass

            if queryset:
                post = request.POST.copy()
                post.update({admin.helpers.ACTION_CHECKBOX_NAME: queryset})
                request._set_post(post)    
        return super(ContaAdmin, self).changelist_view(request, extra_context)


    def has_delete_permission(self, request, obj = None):
        return False 