import json
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required


from webmailufc.gsuiteaccess import Google
from webmailufc.models import LogAcao
from .base import BaseView

import base64
import json

class Requests(BaseView):

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_google_api(self,email):
        if email.split('@')[1].split('.')[0] == Google.ALU_CREDENTIALS[0]:
            return Google(Google.ALU_CREDENTIALS)
        else:
            return Google(Google.SERV_CREDENTIALS)

    def get(self,request):
        result_obj = None
        try:            
            if request.GET.get('method') and request.GET.get('email'):
                google = self.get_google_api(request.GET.get('email'))
            if request.GET.get('method') == 'get-photo':
                result_obj = google.service.users().photos().get(userKey=request.GET.get('email')).execute()
        except:
            result_obj = {}
        return JsonResponse(result_obj)


    def post(self,request):
        data = json.loads(request.body)
        metodo = data['method']
        domains = [self.TIPOS_CONTA[self.DISCENTE][1:],self.TIPOS_CONTA[self.SERVIDOR][1:]]

        success = False
        # not settings.DEBUG 

        conta = self.get_conta(data['email'])
        acao = None

        if True and data['email'] and data['email'].split('@')[1] in domains:
            if metodo == 'update-password' and data['password']:
                success = self.new_password(data['email'],data['password'])
                if success:
                    acao = LogAcao.ALTERACAO_SENHA
            if metodo == 'update-personal-data':
                success = self.update_personal_data(data)
                if success:
                    acao = LogAcao.ALTERACAO_DADOS
                    conta.nome = data['name']
                    conta.sobrenome = data['familyName']
                    conta.email_alternativo = data['recoveryEmail']
                    conta.save() 
            if metodo == 'update-photo':
                success = self.patch_photo(data['email'],data['photo'])
                if success:
                    acao = LogAcao.ALTEROU_FOTO

            if success:
                LogAcao(acao=acao,conta=conta).save()                
        elif settings.DEBUG:
            success = True

        return HttpResponse(status=200) if success else HttpResponse(status=500)

    def new_password(self,email,password):
        google = self.get_google_api(email)
        return google.update_password(email,password)
    
    def update_personal_data(self,posted_data):
        google = self.get_google_api(posted_data['email'])
        response = google.update_personal_data(posted_data['email'],{
            'name': {
                'givenName': posted_data['name'],
                'familyName':posted_data['familyName']                
            },
            'recoveryEmail': posted_data['recoveryEmail'],
            'recoveryPhone': posted_data['telephone'].get('number') if posted_data['telephone'].get('ise164') is True else (posted_data['telephone'].get('countryCode')+posted_data['telephone'].get('number'))
        })
        return response
    
    def patch_photo(self, email, photo):
        google = self.get_google_api(email)
        data = photo[photo.index(',')+1:].replace(r'/\//g','_').replace(r'/\+/g','-').replace(r'/\=/g','*')
        result = None      
        try:
            # q = base64string.decode('utf-8')
            # q = q.replace('/','_').replace('+','-').replace('=','*')
            # q = photo.split(',')[0] + ',' + q
            #             
            mimeType = photo[photo.index(':')+1:photo.index(';')].split('/')[1].upper()
            # mimeType = 'base64'
            result = google.service.users().photos().update(userKey=email,body={
                'kind': 'admin#directory#user#photo',
                'photoData': data,
                'primaryEmail': email
            }).execute()
        except Exception as e:
            print(e)
        return result