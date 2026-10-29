from django.contrib import admin
from django.contrib.auth.models import Permission
from django.contrib.admin.views.main import ChangeList
from django.contrib import messages
from redef.models import Pessoa, Conta, Servidor_SI3, Discente_SI3
from .models import LogEntrada, LogAcao, User
from django.contrib.contenttypes.models import ContentType

class MyChangeList(ChangeList):

    def __init__(self, *args, **kwargs):
        admin_obj = args[11]
        super().__init__(*args, **kwargs)
        self.search_placeholder = admin_obj.search_placeholder


class AdminMethods(admin.ModelAdmin):

    def __init__(self, model, admin_site):
        try:
            self.user_type = ContentType.objects.get_for_model(User)
            self.conta_type = ContentType.objects.get_for_model(Conta)
            self.pessoa_type = ContentType.objects.get_for_model(Pessoa)
            self.can_add_discente_perm = Permission.objects.get(content_type = self.user_type,codename = 'can_add_discente')
            self.can_view_discente_perm = Permission.objects.get(content_type = self.user_type,codename = 'can_view_discente')
            self.can_change_discente_perm = Permission.objects.get(content_type = self.user_type,codename = 'can_change_discente')
            self.can_add_servidor_perm =  Permission.objects.get(content_type = self.user_type,codename = 'can_add_servidor')  
            self.can_view_servidor_perm = Permission.objects.get(content_type = self.user_type,codename = 'can_view_servidor')
            self.can_change_servidor_perm = Permission.objects.get(content_type = self.user_type,codename = 'can_change_servidor')
        except:
            pass
        super().__init__(model, admin_site)

    queryset = None
    def get_queryset(self, request):
        if request.method == 'POST' and len(request.POST.get(admin.helpers.ACTION_CHECKBOX_NAME,{})) > 1:
            self.queryset = self.model.objects.filter(id__in=request.POST[admin.helpers.ACTION_CHECKBOX_NAME]).all()
            return self.queryset
        else:
            if not self.queryset:
                return self.model.objects.all()
            else:
                return self.queryset

    def message_user_(self, request, queryset):
        if(len(queryset) == 0):
            messages.info(request, "Não foi encontrado registro(s)")
        else:
            messages.success(request,f"A consulta obteve {len(queryset)} registro(s)")
    
    def get_search_results(self, request, queryset, search_term):
        queryset,use_distinct = super().get_search_results(request, queryset,search_term)
        
        if search_term and len(search_term) > 0:
            try:
                if search_term.isnumeric():
                    if not queryset:
                        # é siape?
                        servidor = Servidor_SI3.objects.using('administrativo').filter(siape=int(search_term)).first()
                        if not servidor:
                            discente = Discente_SI3.objects.using('academico').filter(matricula=int(search_term)).first()
                            if discente:
                                search_term = discente.pessoa.cpf
                        else:
                            search_term = servidor.pessoa.cpf

                    if self.model is Conta:
                        queryset |= self.model.objects.filter(pessoa__cpf=int(search_term))
                    elif self.model is Pessoa:
                        queryset |= self.model.objects.filter(cpf=int(search_term))    
                    elif self.model is LogEntrada:
                        queryset |= self.model.objects.filter(pessoa__cpf=int(search_term))
                    elif self.model is LogAcao:
                        queryset |= self.model.objects.filter(conta__pessoa__cpf=int(search_term))
                    elif self.model is User:
                        queryset |= self.model.objects.filter(usuario_pessoa__cpf=int(search_term))

                else:
                    if self.model is LogAcao:
                        queryset |= self.model.objects.filter(conta__pessoa__usuario__username=search_term)
                            
            except Exception as e:
                pass       
        
        return queryset, use_distinct