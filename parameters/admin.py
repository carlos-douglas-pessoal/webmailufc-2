from django.contrib import admin
from .models import Parametro
from webmailufc.admin_methods import AdminMethods, MyChangeList

@admin.register(Parametro)
class ParametrosLoginAdmin(AdminMethods):

    search_fields = ['nome']        
    list_display = ('nome','descricao','valor','tipo')

    search_placeholder = "nome do parâmetro"

    def get_changelist(self, request, **kwargs):
        return MyChangeList

    def has_delete_permission(self, request, obj = None):
        return True

    def has_add_permission(self, request):
        return True
    
    def has_change_permission(self, request, obj = None):
        return True