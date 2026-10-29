from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.admin.models import LogEntry
from django.contrib.admin.actions import delete_selected as django_delete_selected
from django.contrib.auth.admin import UserAdmin
from django.contrib import messages
from django.contrib.auth.models import Group
from django.conf import settings
from .models import *
from .forms import *
from redef.models import *
from .gsuiteaccess import Google
from django.utils.safestring import mark_safe
import csv
import hashlib
import random
import string
import json
from datetime import datetime
from django.utils import timezone
import pytz

AdminSite.site_header = 'Webmail UFC'
AdminSite.site_title = 'Webmail UFC'
AdminSite.app_index_template = 'admin/base.html'
admin.site.disable_action('delete_selected')

from .admin_methods import AdminMethods, MyChangeList


@admin.register(LogEntry)
class AdminLog(AdminMethods):
    list_per_page = 25
    
    search_fields = ['user__username__icontains','object_repr__icontains']
    list_display = ('action_time','user','object_id','object_repr','action_flag','change_message','content_type')

    def has_delete_permission(self, request, obj = None):
        return False

    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj = None):
        return False 


@admin.register(LogEntrada)
class LogEntradaAdmin(AdminMethods):    
    list_per_page = 10
    list_display = ('get_data_e','get_data_s', 'get_login', 'pessoa','ip','user_agent')
    search_fields = ['pessoa__full_nome__icontains','pessoa__usuario__username__icontains','data_e__icontains']

    search_placeholder = "login, data de entrada, nome, CPF, siape ou matrícula"

    def get_changelist(self, request, **kwargs):
        return MyChangeList

    def changelist_view(self, request, extra_context=None):
        extra_context = {'title': 'Selecione um registro de entrada para visualizar'}
        return super(LogEntradaAdmin, self).changelist_view(request, extra_context)

    def has_delete_permission(self, request, obj = None):
        return False

    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj = None):
        return False 

@admin.register(LogAcao)
class LogAcaoAdmin(AdminMethods):
    list_per_page = 10
    list_display = ('get_data_acao','acao','conta','get_login','get_pessoa_acao')
    search_fields = ['conta__pessoa__full_nome__icontains','conta__email__icontains']

    search_placeholder  = 'nome, login, CPF, e-mail ou siape'

    def get_changelist(self, request, **kwargs):
        return MyChangeList

    def changelist_view(self, request, extra_context=None):
        extra_context = {'title': 'Selecione um registro para visualizar'}
        return super(LogAcaoAdmin, self).changelist_view(request, extra_context)

    def has_delete_permission(self, request, obj = None):
        return False

    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj = None):
        return False 

@admin.register(User)
class CustomUserAdmin(AdminMethods):

    list_per_page = 10
    list_display = ('username','email','get_nome','is_staff','is_superuser')
    search_fields = ('username__icontains','email__icontains','first_name__icontains')
    search_placeholder = "usuário, nome da pessoa, e-mail,siape ou matrícula"

    def get_changelist(self, request, **kwargs):
        return MyChangeList

    def has_change_permission(self, request, obj = None):
        return True 

    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj = None):
        return False 

@admin.register(ImportacaoContas)
class ImportacaoContasCSVAdmin(AdminMethods):
    form = ContasCSVForm
    list_per_page = 10
    list_display = ('get_nome_arquivo','data_cadastro','cadastrado_por','processado')
    actions = ['processar_arquivo','delete_selected']

    def changelist_view(self, request, extra_context=None):
        extra_context = {'title': 'Selecione um arquivo para visualizar'}
        return super(ImportacaoContasCSVAdmin, self).changelist_view(request, extra_context)

    def delete_selected(modeladmin, request, queryset):
        return django_delete_selected(modeladmin, request, queryset)
    delete_selected.short_description = "Remover Arquivo(s) selecionado(s)"

    def has_delete_permission(self, request, obj = None):
        return True

    def has_add_permission(self, request):
        return True
    
    def has_change_permission(self, request, obj = None):
        return False  

    def processar_arquivo(self, request, queryset):
        try:
            queryset = queryset.filter(processado=False)
            if not queryset:
                messages.error(request, "Este arquivo já foi importado")
                return
            for arquivo in queryset:
                ProcessadorArquivoCSV.processar(arquivo,request.user)
            criticas = arquivo.criticas.all()
            messages.success(request, f"Os dados foram importados! Existem {len(criticas)} críticas.")
        except Exception as Ex:
            print(Ex)
            messages.error(request,mark_safe(f"Não foi possível importar os dados <br> {str(Ex)}"))
    processar_arquivo.short_description = "Processar Arquivo"  

    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super(ImportacaoContasCSVAdmin, self).get_form(request, obj, **kwargs)
        class ImportacaoContasCSVAdminWithRequest(AdminForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return AdminForm(*args, **kwargs)
        return ImportacaoContasCSVAdminWithRequest

@admin.register(CriticaImportacaoContas)
class CriticaArquivoImportacaoCSV(admin.ModelAdmin):
    list_per_page = 50
    search_fields = ['linha']
    list_display = ('linha','arquivo')

    def changelist_view(self, request, extra_context=None):
        extra_context = {'title': 'Selecione uma linha para visualizar'}
        return super(CriticaArquivoImportacaoCSV, self).changelist_view(request, extra_context)

    def has_delete_permission(self, request, obj = None):
        return True

    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj = None):
        return False 

from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import ADDITION
from .logging import WebmailUFCLogging
from redef.helper import LoginHelper
from django.db.models import Q
from django.contrib.auth.models import Permission
class ProcessadorArquivoCSV:

    @staticmethod
    def convert_to_datetime(string):
        q = pytz.timezone('America/Fortaleza')
        return q.localize(datetime.strptime(string,'%Y-%m-%d %H:%M'))


    @staticmethod
    def processar(arquivo,user):
        conta_type = ContentType.objects.get_for_model(Conta)
        pessoa_type = ContentType.objects.get_for_model(Pessoa)
        user_type = ContentType.objects.get_for_model(User) 

        can_add_discente_perm = Permission.objects.get(content_type = user_type,codename = 'can_add_discente')
        can_view_discente_perm = Permission.objects.get(content_type = user_type,codename = 'can_view_discente')
        can_change_discente_perm = Permission.objects.get(content_type = user_type,codename = 'can_change_discente')
        can_add_servidor_perm =  Permission.objects.get(content_type = user_type,codename = 'can_add_servidor')  
        can_view_servidor_perm = Permission.objects.get(content_type = user_type,codename = 'can_view_servidor')
        can_change_servidor_perm = Permission.objects.get(content_type = user_type,codename = 'can_change_servidor')

        admin_user = None
        try:
            admin_user = User.objects.get(username='admin')
        except:
            admin_user = user

        with open(arquivo.csv.url,newline='',encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            count = 1
            g_s = Group.objects.get(name='Servidores')
            g_d = Group.objects.get(name='Alunos')
            login_helper = LoginHelper()
            for row in reader:                

                pessoa_si3_discente = None
                pessoa_si3_servidor = None
                pessoa_si3 = None

                if row['cpf'] is not None and len(row['cpf']) != 0:
                    pessoa_si3_discente = Pessoa_SI3.objects.using('academico').filter(cpf=row['cpf']).first()
                    pessoa_si3_servidor = Pessoa_SI3.objects.using('administrativo').filter(cpf=row['cpf']).first()
                    pessoa_si3 = pessoa_si3_discente or pessoa_si3_servidor          

                pessoa = None
                conta = None
                usuario = None
                user_db = None
                suspenso = False
                setorial = False 

                if not row['cpf'] or len(row['cpf']) == 0  or not row['email_ufc'] or pessoa_si3 is None or ('@' not in row['email_ufc']):
                    if CriticaImportacaoContas.objects.filter(linha=json.dumps(row,default=str)).count() == 0:
                        CriticaImportacaoContas(linha=json.dumps(row,default=str),arquivo=arquivo).save()
                    if not row['email_ufc']:
                        continue
                    try:
                        Conta.objects.using('default').get(email=row['email_ufc'])
                    except:
                        __data = None
                        try:
                            if row['data_cadastro'] is not None:
                                __data = ProcessadorArquivoCSV.convert_to_datetime(row['data_cadastro'][:16])
                        except:
                            __data = timezone.now()
                        conta = Conta(nome=row['nome_config'],sobrenome=row['sobrenome_config'],email=row['email_ufc'],
                                email_alternativo=row['email_alternativo'],data_cadastro=__data,setorial=setorial,
                                    suspenso=suspenso,pessoa=admin_user.usuario_pessoa)
                        conta.save()
                        critica_str = None
                        if not row['cpf']:
                            critica_str = f"{row['email_ufc']} sem CPF"
                        elif len(row['cpf']) == 0:
                            critica_str = f"CPF não pode estar vazio! Email: {row['email_ufc']}"
                        elif '@' not in row['email_ufc']:
                            critica_str = f"Registro com email inválido. CPF: {row['cpf']}"
                        elif not pessoa_si3:
                            critica_str = f"Registro de pessoa sem vínculo com a UFC. CPF: {row['cpf']}"
                        elif not row['email_ufc']:
                            critica_str = f"Registro sem email {row['cpf']}"
                        WebmailUFCLogging.log(user,conta_type,conta.id,str(conta), ADDITION, critica_str)
                    continue

                try:
                    pessoa = Pessoa.objects.get(cpf=row['cpf'])
                except Pessoa.DoesNotExist:
                    usuario = getattr(pessoa_si3,"pessoa_usuario",None)
                    if not usuario:
                        user_,domain = row['email_ufc'].split('@')
                        pwd = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(8))
                        usuario = Usuario_SI3(login=f"{user_}.{row['cpf']}",senha=hashlib.md5(pwd.encode()).hexdigest())

                    usuario = usuario or pessoa.usuario
                    if not usuario:
                        usuario = pessoa.usuario
                    
                    try:
                        user_db = User.objects.get(username=usuario.login)
                    except User.DoesNotExist:
                        user_db = User(username=usuario.login,first_name=pessoa_si3.nome,email=pessoa_si3.email or row['email_ufc'],is_staff=False,is_superuser=False,is_active=True)
                        user_db.set_password(usuario.senha)
                        try:
                            user_db.save()
                            WebmailUFCLogging.log(user,user_type,user_db.id,str(user_db), ADDITION)
                        except Exception as e0:
                            print(e0)
                        
                    pessoa = Pessoa(cpf=row['cpf'],full_nome=pessoa_si3.nome,usuario=user_db)
                    try:
                        pessoa.save()
                        WebmailUFCLogging.log(user,pessoa_type,pessoa.id,str(pessoa), ADDITION)
                    except Exception as e1:
                        print(e1)                
                
                try:
                    conta = Conta.objects.get(email=row['email_ufc'])
                except Conta.DoesNotExist:
                    if not row.get('suspenso') or row.get('suspenso') == 'f':
                        suspenso = False
                    else:
                        suspenso = True
                    if not row.get('setorial') or row.get('setorial') == 'f':
                        setorial = False
                    else:
                        setorial = True

                    data_cad = timezone.now()

                    try:
                        if row['data_cadastro'] is not None and len(row['data_cadastro']) > 0:
                            data_cad = ProcessadorArquivoCSV.convert_to_datetime(row['data_cadastro'][:16])
                    except Exception as e:
                        print(e)

                    conta = Conta(nome=row['nome_config'],sobrenome=row['sobrenome_config'],email=row['email_ufc'],
                                email_alternativo=row['email_alternativo'],data_cadastro=data_cad,setorial=setorial,
                                    suspenso=suspenso,pessoa=pessoa)
                    try:
                        conta.save()
                        WebmailUFCLogging.log(user,conta_type,conta.id,str(conta), ADDITION)
                    except Exception as e2:
                        print(e2) 
                
                has_disc_perm = False
                has_serv_perm = False

                if  (not pessoa.usuario.has_perm(f"{can_view_discente_perm.content_type.app_label}.{can_view_discente_perm.codename}")) and pessoa_si3_discente and len(pessoa_si3_discente.discente_pessoa.filter(~Q(status__status__in=login_helper.IDS_SIT_DISC_EXCLUIDO) & Q(tipo__in=login_helper.IDS_TIPO_DISCENTE)).all()) > 0:
                    if(len(pessoa_si3_discente.discente_pessoa.filter(Q(status__status__in=login_helper.IDS_DISCENTE_STATUS_ATIVO) & Q(tipo__in=login_helper.IDS_TIPO_DISCENTE)).all()) > 0):
                        pessoa.usuario.user_permissions.add(can_add_discente_perm)
                    pessoa.usuario.user_permissions.add(can_view_discente_perm)
                    pessoa.usuario.user_permissions.add(can_change_discente_perm)
                    has_disc_perm = True
                    g_d.user_set.add(pessoa.usuario)
                    WebmailUFCLogging.log(user,user_type,pessoa.usuario.id,str(pessoa.usuario), ADDITION,f'[Discente] Usuário recebeu permissoes de {can_view_discente_perm.codename},{can_change_discente_perm.codename}' + ((f",{can_add_discente_perm.codename}") if pessoa.usuario.has_perm(can_add_discente_perm) else "") + " contas")

                if (not pessoa.usuario.has_perm(f"{can_view_servidor_perm.content_type.app_label}.{can_view_servidor_perm.codename}")) and pessoa_si3_servidor and len(pessoa_si3_servidor.servidor_pessoa.filter(ativo__permite_acesso_sist_rh=True).all()) > 0:
                    if len(pessoa_si3_servidor.servidor_pessoa.filter(Q(ativo__id_ativo__in=login_helper.IDS_SERV_ATIVO) & Q(situacao__id_situacao__in=login_helper.IDS_SERVIDOR_SITUACAO_PERMITE_CRIAR) ).all()) > 0:
                        pessoa.usuario.user_permissions.add(can_add_servidor_perm)                        
                    pessoa.usuario.user_permissions.add(can_view_servidor_perm)
                    pessoa.usuario.user_permissions.add(can_change_servidor_perm)
                    has_serv_perm = True
                    g_s.user_set.add(pessoa.usuario)
                    WebmailUFCLogging.log(user,user_type,pessoa.usuario.id,str(pessoa.usuario), ADDITION,f'[Servidor] Usuário recebeu permissoes de {can_view_servidor_perm.codename},{can_change_servidor_perm.codename}' + ((f",{can_add_servidor_perm.codename}") if pessoa.usuario.has_perm(can_add_servidor_perm) else "") + " contas")               

                if ('alu.ufc.br' == row['email_ufc'].split('@')[1]) and not has_disc_perm and not pessoa.usuario.has_perm(f"{can_view_discente_perm.content_type.app_label}.{can_view_discente_perm.codename}"):
                    pessoa.usuario.user_permissions.add(can_change_discente_perm)
                    pessoa.usuario.user_permissions.add(can_view_discente_perm)
                    WebmailUFCLogging.log(user,user_type,pessoa.usuario.id,str(pessoa.usuario), ADDITION,'Usuário sem vínculo de aluno porém possui conta de aluno (Foi atribuída permissão para ver e editar conta)')
                elif ('ufc.br' == row['email_ufc'].split('@')[1]) and not has_serv_perm and not pessoa.usuario.has_perm(f"{can_view_servidor_perm.content_type.app_label}.{can_view_servidor_perm.codename}"):
                    pessoa.usuario.user_permissions.add(can_change_servidor_perm)
                    pessoa.usuario.user_permissions.add(can_view_servidor_perm)
                    WebmailUFCLogging.log(user,user_type,pessoa.usuario.id,str(pessoa.usuario), ADDITION,'Usuário sem vínculo de servidor porém possui conta de servidor (Foi atribuída permissão para ver e editar conta)')   

                str_ = f"{count} - {pessoa_si3} importado!"
                print(str_)                
                count = count + 1
        arquivo.processado = True
        arquivo.save()