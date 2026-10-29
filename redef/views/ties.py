from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Q

from .base import BaseView

class VinculoView(BaseView):
    template_name = 'ties.html'

    @method_decorator(login_required)     
    def dispatch(self, request, *args, **kwargs):
        if self.is_servidor_ativo and self.is_discente_ativo:
            return super(VinculoView, self).dispatch(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('redef:login'))

      

    def get(self,request):
        tipo = request.GET.get('tipo')
        contas = None
        if tipo and tipo.lower() in ['servidor','discente']:
            if tipo.lower() == 'servidor':
                contas = self.get_contas(servidor=True)
            elif tipo.lower() == 'discente':
                contas = self.get_contas(discente=True)
            if len(contas) > 0:
                return HttpResponseRedirect(reverse('redef:redefinir') + f'?tipo={tipo}')
            else:
                return HttpResponseRedirect(reverse('redef:cadastro') + f'?tipo={tipo}')
        return render(request,self.template_name)