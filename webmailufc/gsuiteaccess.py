import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import string
import random
from datetime import datetime
import logging

class Google:
    
    logger = logging.getLogger('django')

    ALU_CREDENTIALS = ('alu','drc@dominioalu.ufc.br')
    SERV_CREDENTIALS = ('serv','drc@ufc.br')
    STI_UFC_BR_CREDENTIALS = ('sti_ufc_br','drc@sti.ufc.br')

    SERVICE_ACCOUNTS_ = {
        ALU_CREDENTIALS: 'alu_ufc_br',
        SERV_CREDENTIALS: 'ufc_br',
        STI_UFC_BR_CREDENTIALS: 'sti_ufc_br'
    }

    GOOGLE_SALA_DE_AULA_GROUP = 'professores_do_googlesaladeaula@ufc.br'

    SCOPES = ['https://www.googleapis.com/auth/admin.directory.user','https://www.googleapis.com/auth/admin.directory.group']    

    delegated_credentials = None
    service = None
    
    STI_UFC_BR_DOMAINS = (
        'cea.ufc.br',
        'memorial.ufc.br',
        'procult.ufc.br',
        'sti.ufc.br',
    )
    

    @staticmethod
    def get_credentials(email):
        user,domain = email.split('@')
        if 'alu' in domain:
            return Google.ALU_CREDENTIALS
        elif domain in Google.STI_UFC_BR_DOMAINS:
            return Google.STI_UFC_BR_CREDENTIALS
        return Google.SERV_CREDENTIALS

    def __init__(self,credentials):

        email_impersonation = ''

        key = self.SERVICE_ACCOUNTS_[credentials]
        email_impersonation = credentials[1]
        
        credentials = service_account.Credentials.from_service_account_file(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),f"webmailufc/keys/{key}.json"),scopes=self.SCOPES)

        self.delegated_credentials = credentials.with_subject(email_impersonation) 

        self.service = build('admin','directory_v1',credentials=self.delegated_credentials)
        # results = self.service.users().list(customer='my_customer',maxResults=10,orderBy='email').execute()

        # users = results.get('users',[])

        # for user in users:
        #     print(user['primaryEmail'])
        

    def exists(self,email):
        try:
            result = self.service.users().get(userKey=email).execute()
            return result
        except Exception as ex:
            return None

    def insert(self,primaryEmail,givenName,familyName,recoveryEmail,recoveryPhone):
        try:
            pwd = self.create_password()
            user_body = {
                'primaryEmail': primaryEmail,
                'name': {
                    'givenName': givenName,
                    'familyName': familyName,
                },
                'password': pwd,
                'changePasswordAtNextLogin': True,
                'recoveryEmail': recoveryEmail
            }
            if recoveryPhone:
                user_body['recoveryPhone'] = recoveryPhone
            domain = ''
            try:
                domain = primaryEmail.split('@')[1]
            except:
                pass
            if domain == 'alu.ufc.br':
                user_body['orgUnitPath'] = '/ALU'
            elif domain == 'ufc.br':
                user_body['orgUnitPath'] = '/'
                
            insert_user = self.service.users().insert(body=user_body).execute()
            try:
                if domain == 'ufc.br':
                    self.insert_user_in_group(primaryEmail,self.GOOGLE_SALA_DE_AULA_GROUP)
            except Exception as ex:
                self.logger.error(f"\n[{primaryEmail}] [{datetime.now()}] Erro ao inserir usuário no Google Classroom\n>> {str(e)}") 
            return insert_user,pwd
        except Exception as e:
            self.logger.error(f"\n[{primaryEmail}] [{datetime.now()}] API: erro ao criar conta\n>> {str(e)}")   
    
    def suspend(self,email,is_suspended):
        try:
            updated_user = self.service.users().update(userKey=email,body={'suspended':is_suspended}).execute()
            return updated_user
        except:
            return None

    def update_password(self,email,password):
        try:
            user_body = { 'password': password }
            updated_user = self.service.users().update(userKey=email,body=user_body).execute()
            return updated_user
        except:
            return None

    def update_personal_data(self,email,data):
        try:
            updated_user = self.service.users().update(userKey=email,body=data).execute()
            return updated_user
        except:
            return None

    def create_password(self):
        return ''.join(random.choice(string.ascii_letters + string.digits) for i in range(8))  

    def insert_user_in_group(self,email,group):
        try:
            member = self.service.members().insert(groupKey=group,body={
                "role": "MEMBER",
                "email": email
            }).execute()
            return member
        except Exception as e:
            return None
        
