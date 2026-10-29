from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .base import BaseView



class SuccessView(BaseView):

    template_name = "success.html"

    user = None

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('credentials'):
            return HttpResponseRedirect(reverse('redef:redefinir'))
        self.user = request.session['credentials']
        del request.session['credentials']
        return super().dispatch(request, *args, **kwargs)
    
    def get(self,request):
        return render(request,self.template_name,{
            'email': self.user['user'],
            'password': self.user['password']
        })