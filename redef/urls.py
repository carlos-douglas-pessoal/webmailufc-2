from django.urls import path
from django.views.generic.base import RedirectView
from .views.login import LoginView, logout_
from .views.ties import VinculoView
from .views.signup import SignUpView
from .views.redefine import RedefineView
from .views.success import SuccessView
from .views.reqs import Requests

urlpatterns = [
    path('', RedirectView.as_view(url='/login/',permanent=False) ,name='index'),
    path('login/', LoginView.as_view(),name='login'),
    path('logout/',logout_,name='logout'),
    path('vinculos/',VinculoView.as_view(),name='vinculos'),
    path('cadastro/',SignUpView.as_view(),name='cadastro'),
    path('redefinir/',RedefineView.as_view(),name='redefinir'),
    path('sucesso/',SuccessView.as_view(),name='sucesso'),
    path('requests/',Requests.as_view(),name='requests')
]