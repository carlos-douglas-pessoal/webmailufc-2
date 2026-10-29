from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect

# Create your views here.


def default_404(request, exception, template_name="404.html"):
    return render(request,template_name)

def default_500(request, template_name="500.html"):
    return render(request,template_name)
