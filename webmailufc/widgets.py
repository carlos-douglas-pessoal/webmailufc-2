from django.contrib.auth.mixins import LoginRequiredMixin
from django_select2.views import AutoResponseView
from django_select2.forms import ModelSelect2Widget
from redef.models import Pessoa

class Select2ViewSecured(LoginRequiredMixin, AutoResponseView):
    pass

class PessoaSelect2WidgetMixin(object):
    def __init__(self, *args, **kwargs):
        kwargs['data_view'] = 'user-select2-view'
        super(PessoaSelect2WidgetMixin, self).__init__(*args, **kwargs)

class PessoaWidget(PessoaSelect2WidgetMixin, ModelSelect2Widget):
    # model = Pessoa
    search_fields = ['full_nome__icontains','cpf__istartswith','cpf__icontains']