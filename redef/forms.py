from django.forms import *
from .models import *
from .helper import *
from webmailufc.gsuiteaccess import Google
from webmailufc.models import User
from django import forms
from django.core.validators import RegexValidator
from django.contrib import messages
from webmailufc.utils import enviar_senha
from django_select2 import forms as s2forms
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.db.models.fields.related import ManyToOneRel
from django.contrib import admin
from datetime import datetime
import re

alias_usuario_validator = RegexValidator(regex=r'^([a-z]{7,}|[a-z]{3,}(\.[a-z]{3,}|\.?[a-z]{2,}[0-9]{2}([a-z]{2,})?|[0-9]{2}([a-z]{3,})|[0-9]{4}([a-z]{2,})|\.?[a-z]{2,}[0-9]{4}([a-z]{2,})?|\.?[0-9]{4}))$',message='E-mail não segue o padrão de criação @ufc.br e @alu.ufc.br')
regex = re.compile('^([a-z]{7,}|[a-z]{3,}(\.[a-z]{3,}|\.?[a-z]{2,}[0-9]{2}([a-z]{2,})?|[0-9]{2}([a-z]{3,})|[0-9]{4}([a-z]{2,})|\.?[a-z]{2,}[0-9]{4}([a-z]{2,})?|\.?[0-9]{4}))$')

class CPFWidget(TextInput):
    def __init__(self, attrs=None):
        return super(CPFWidget, self).__init__(attrs)

    class Media:
        js = ['js/cpf-widget.js']

class PessoaForm(ModelForm):

    full_nome = CharField(label='Nome Completo',required=False,disabled=True,widget=TextInput(attrs={'style':'width:30em'}))    
    siape = CharField(label='Siape Servidor',required=False,widget=TextInput(attrs={'style':'width:10em'}),help_text="Matrícula Siape (Caso servidor)")
    matricula_sigaa = CharField(label="Matrícula SIGAA",required=False,widget=TextInput(attrs={'style':'width:10em'}),help_text="Matrícula Ativa do SIGAA (Caso aluno)")
    cpf = CharField(label="CPF",required=False,max_length=11,widget=CPFWidget(attrs={'style':'width:10em'}),help_text="CPF")
    situacao_servidor = CharField(label='Situação',required=False,widget=TextInput(attrs={'style':'width:10em'}))
    status_discente = CharField(label='Status Discente',required=False,widget=TextInput(attrs={'style':'width:10em'}))
    status_servidor = CharField(label='Status Servidor',required=False,widget=TextInput(attrs={'style':'width:10em'}))    

    discente = None
    servidor = None
    pessoa = None
    TypeForm = None

    def __init__(self, *args, **kwargs):    
        super(PessoaForm, self).__init__(*args,**kwargs)
        self.login_helper = LoginHelper()       
        instance = getattr(self, 'instance', None)            
        # self.fields['full_nome'].label = 'Nome Completo'
        self.fields['cpf'].label = 'CPF'
        self.fields['cpf'].required = False
        if instance and instance.pk:            
            self.fields['cpf'].disabled = True
            self.discente = self.login_helper.get_discente({'pessoa__cpf':instance.cpf}, return_object=False)
            self.servidor = self.login_helper.get_servidor({'pessoa__cpf':instance.cpf}, inclui_aposentados=True,return_object=False)
            self.fields['cpf'].widget.max_length = 20
            # self.initial['cpf'] = instance.cpf_text
            if self.discente:
                if self.discente.filter(status__status__in=self.login_helper.IDS_DISCENTE_STATUS_ATIVO).count() > 0:
                    self.discente = self.discente.filter(status__status__in=self.login_helper.IDS_DISCENTE_STATUS_ATIVO).first()
                else:
                    self.discente = self.discente.first()

                if self.discente.status.status not in self.login_helper.IDS_DISCENTE_STATUS_ATIVO:
                    self.instance.matricula_sigaa = mark_safe(f"<div style='color:red;font-weight:bold'>{self.discente.matricula}</div>")
                else:
                    self.instance.matricula_sigaa = self.discente.matricula
                self.instance.status_discente = self.discente.status.descricao
            else:
                self.fields['matricula_sigaa'].widget = HiddenInput()
                self.fields['status_discente'].widget = HiddenInput()
            if self.servidor:
                if self.servidor.filter(ativo__id_ativo__in=self.login_helper.IDS_SERV_ATIVO).count() > 0:
                    self.servidor = self.servidor.filter(ativo__id_ativo__in=self.login_helper.IDS_SERV_ATIVO).first()
                else:
                    self.servidor = self.servidor.first()

                if self.servidor.ativo.id_ativo not in self.login_helper.IDS_SERV_ATIVO:
                    self.instance.siape = mark_safe(f"<div style='color:red;font-weight:bold'>{self.servidor.siape}</div>")
                else:
                    self.instance.siape = self.servidor.siape
                self.instance.situacao_servidor = self.servidor.situacao.descricao
                self.instance.status_servidor = self.servidor.ativo.descricao
                # self.initial['siape'] = self.servidor.siape                
                # self.fields['siape'].disabled = True
            else:
                self.fields['siape'].widget = HiddenInput()
                self.fields['situacao_servidor'].widget = HiddenInput()
                self.fields['status_servidor'].widget = HiddenInput()
        else:
            self.fields['full_nome'].widget = HiddenInput()  
            self.fields['status_discente'].widget = HiddenInput()
            self.fields['status_servidor'].widget = HiddenInput()
            self.fields['situacao_servidor'].widget = HiddenInput()
            self.TypeForm = 'create'          
            


        # self.fields['usuario'].widget.widget.attrs.update({'disabled':True})
        # self.fields['usuario'].required = False
        # self.fields['usuario'].widget.can_add_related = False
        # self.fields['usuario'].widget.can_change_related = False
        # self.fields['usuario'].widget.can_delete_related = False

        # self.fields['full_nome'].widget.attrs['disabled'] = True
        # self.fields['full_nome'].required = False
        
        
        # if instance and instance.pk:            
        #     self.fields['usuario'].required = False
        #     self.fields['usuario'].widget.widget.attrs.update({'disabled':True})
        #     self.fields['usuario'].widget.can_add_related = False
        #     self.fields['usuario'].widget.can_change_related = False
        #     self.fields['usuario'].widget.can_delete_related = False


    def save(self,commit=True):
        if self.instance and not self.instance.pk:
            usuario_si3 = self.pessoa.pessoa_usuario
            try:
                user = User.objects.get(username=usuario_si3.login)
            except User.DoesNotExist:
                pessoa_si3 = usuario_si3.pessoa
                user = self.login_helper.create_user({
                    'username': usuario_si3.login,
                    'name':pessoa_si3.nome,
                    'email':pessoa_si3.email, 
                    'is_staff':False, 'is_superuser':False, 'is_active':True,
                    'password': usuario_si3.senha
                },self.servidor, self.discente)            

            self.instance.full_nome = self.pessoa.nome
            self.instance.cpf = self.pessoa.cpf
            self.instance.id_institucional = self.pessoa.id_institucional
            self.instance.usuario = user

        return super().save(commit)
    
    def clean(self):
        if self.instance and self.instance.pk:
            raise ValidationError("Apenas é possível adicionar novas pessoas")

        if self.discente or self.servidor:
            self.pessoa = (self.discente or self.servidor).pessoa 
        if not self.pessoa:
            raise forms.ValidationError("Ocorreu um erro ao importar os dados do SI3")

        if len(Pessoa.objects.filter(cpf=self.pessoa.cpf)) > 0:
            raise forms.ValidationError(f"\"{self.pessoa.nome}\" - essa pessoa já está cadastrada na base de dados.")
        return super().clean()

    def clean_cpf(self):
        if self.instance and self.instance.pk:
            return self.instance.cpf
        if self.cleaned_data['cpf']:
            if not self.cleaned_data['cpf'].isnumeric():
                self.add_error('cpf','Deve conter apenas números')
                return None
            self.servidor = self.login_helper.get_servidor({'pessoa__cpf': self.cleaned_data['cpf']},inclui_aposentados=True, return_object=True)
            self.discente = self.login_helper.get_discente({'pessoa__cpf': self.cleaned_data['cpf']},ativo_apenas=False, return_object=True)
            if not self.servidor and not self.discente:
                self.add_error('cpf','Não foi encontrado um vínculo ativo com instituição!')
                return None  
            pessoa_si3 = (self.servidor or self.discente).pessoa
            self.verify_pessoa(pessoa_si3.cpf,"cpf")          
        return self.cleaned_data.get('cpf')
    
    def clean_full_nome(self):
        if self.pessoa:
            return self.pessoa.full_nome
        else:
            return self.cleaned_data['full_nome']

    def clean_matricula_sigaa(self):
        if self.cleaned_data['matricula_sigaa']:
            self.discente = self.login_helper.get_discente({'matricula': self.cleaned_data['matricula_sigaa']},ativo_apenas=False,return_object=True)
            if not self.discente:
                self.add_error("matricula_sigaa","Matrícula inválida ou discente não possui vínculo com a instituição.")
                return None
            self.verify_pessoa(self.discente.pessoa.cpf,"matricula_sigaa")
        return self.cleaned_data.get('matricula_sigaa')
    
    def verify_pessoa(self,cpf,field):
        pessoa = Pessoa.objects.filter(cpf=cpf).first()
        if pessoa:
            self.add_error(field,f"A pessoa {pessoa.full_nome} já se encontra cadastrada no sistema")
        return None 
    
    def clean_siape(self):
        if self.cleaned_data['siape']:
            self.servidor = self.login_helper.get_servidor({'siape': self.cleaned_data['siape']},inclui_aposentados=True,return_object=True)
            if not self.servidor:
                self.add_error("siape","Siape inválido ou servidor não possui vínculo com a instituição.")
                return None
            self.verify_pessoa(self.servidor.pessoa.cpf,"siape")
        return self.cleaned_data.get('siape')
    
    def clean_usuario(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.usuario
        else:
            return self.cleaned_data['usuario']

    class Meta:
        model = Pessoa
        # exclude = ('id','cpf',)
        fields = ['full_nome','cpf','siape','matricula_sigaa','status_discente','situacao_servidor','status_servidor']

        widgets = {
            'usuario': Select()
        }

from webmailufc.widgets import PessoaWidget
class ContaForm(ModelForm):

    nome = CharField(widget=TextInput(attrs={'style':'width:30em'}),help_text="O nome do usuário no Gmail")
    sobrenome = CharField(widget=TextInput(attrs={'style':'width:30em'}),help_text="O sobrenome do usuário no Gmail")
    email = EmailField(widget=EmailInput(attrs={'style':'width:30em'}),help_text="Email com o domínio ufc.br")
    email_alternativo = EmailField(label="E-mail Alternativo",widget=EmailInput(attrs={'style':'width:30em','required':True}),help_text=mark_safe("E-mail de recuperação. <strong>A senha será enviada para este e-mail em caso de criação ou redefinição.</strong>"))
    # pessoa =  ModelChoiceField(queryset=Pessoa.objects.all(),label="Pessoa",widget=s2forms.ModelSelect2Widget(attrs={'data-width':'30em','data-placeholder':'Utilize o nome ou o cpf para buscar uma pessoa'},model=Pessoa,search_fields=['full_nome__istartswith','cpf__istartswith']),help_text="A pessoa que possui a conta")
    pessoa = ModelChoiceField(queryset=Pessoa.objects.all(),label="Pessoa",widget=PessoaWidget(attrs={'data-language': 'pt-BR','data-width':'30em','data-placeholder':'Utilize o nome ou o cpf para buscar uma pessoa'}),help_text="A pessoa que possui a conta")
    suspenso = BooleanField(help_text='Suspender conta no Gmail',required=False,label=mark_safe("<div style='color:red;font-weight:bold'>Suspender</div>"))
    setorial = BooleanField(help_text='Indica se o e-mail é setorial',required=False)
    apenas_salvar = BooleanField(label='Apenas inserir no banco de dados',required=False,help_text=mark_safe('<strong>Selecione essa opção se deseja apenas inserir a conta no banco (não criar no GSuite)</strong>'))

    TypeForm = None    

    def __init__(self, *args, **kwargs):       
        super(ContaForm, self).__init__(*args,**kwargs)
        instance = getattr(self, 'instance', None)    
        rel = Pessoa._meta.related_objects[0]
        self.fields['pessoa'].widget = RelatedFieldWidgetWrapper(self.fields['pessoa'].widget, rel, admin.site)
        if instance and instance.pk:
            self.fields['email'].required = False
            self.fields['email'].widget.attrs['disabled'] = True
            if not self.instance.setorial:
                self.fields['pessoa'].required = False
                self.fields['pessoa'].disabled = True
            # self.fields['pessoa'].widget.widget.attrs.update({'disabled':True})
                self.fields['pessoa'].widget.can_add_related = False
                self.fields['pessoa'].widget.can_change_related = False
                self.fields['pessoa'].widget.can_delete_related = False
            self.fields['email_alternativo'].widget.attrs['required'] = False
            self.TypeForm = 'update'
        elif instance:
            self.TypeForm = 'create'
            # self.fields['pessoa'].widget.can_edit_related = False
            # self.fields['pessoa'].widget.can_add_related = True

      
    def save(self,commit=True):        
        return super(ContaForm, self).save(commit)

    def clean_email_alternativo(self):
        return self.cleaned_data['email_alternativo']

    def clean_email(self):
        if self.instance and not self.instance.pk:
            user,domain = self.cleaned_data['email'].split('@')
            if 'ufc.br' not in domain:
                self.add_error('email',"O e-mail não parece ter um domínio válido! Só é aceito apenas @alu.ufc.br ou @ufc.br.")
                raise forms.ValidationError("")
            # if regex.match(user) is None:
            #     self.add_error('email',mark_safe(f'E-mail não segue o padrão de criação @ufc.br e @alu.ufc.br. <br/> A quantidade mínima de caracteres no nome de usuário é 7. Você pode usar, por exemplo: <br/>- nome55sobrenome@{domain}<br>- nome1985sobrenome@{domain}<br>- nome.sobrenome@{domain}'))
            #     return None
            # if 'alu' in domain:
            #     google = Google(Google.ALU_CREDENTIALS)
            # else:
            #     google = Google(Google.SERV_CREDENTIALS)
            # if google.exists(self.cleaned_data['email']) and not self.cleaned_data['apenas_salvar']:
            #     self.add_error('email',f"O e-mail {self.cleaned_data['email']} já existe!")
            #     raise forms.ValidationError("")    
        return self.cleaned_data['email'] or self.instance.email

    def clean_apenas_salvar(self):
        return self.cleaned_data['apenas_salvar']

    def clean_pessoa(self):
        # instance = getattr(self, 'instance', None)
        # if instance and instance.pk:
        #     return instance.pessoa
        # else:
        return self.cleaned_data['pessoa']   

    def clean(self):    
        user,domain = self.cleaned_data['email'].split('@')
        if 'alu' in domain:
            google = Google(Google.ALU_CREDENTIALS)
        else:
            google = Google(Google.SERV_CREDENTIALS)
        if self.cleaned_data['apenas_salvar']:
            if not google.exists(self.cleaned_data['email']):
                raise forms.ValidationError("O email não se encontra cadastrado no GSuite. Por favor,desmarque a opção 'Apenas salvar no banco de dados'.")
            else:
                return super(ContaForm, self).clean()
        elif google.exists(self.cleaned_data['email']):
            self.add_error('email',f"O e-mail {self.cleaned_data['email']} já existe!")
            raise forms.ValidationError("")         
        return super(ContaForm, self).clean()

    class Meta:
        exclude = ('id',)
        model = Conta
        fields = ('pessoa','nome','sobrenome','email','email_alternativo','suspenso','setorial')

    class Media:
        js = ['https://code.jquery.com/jquery-3.5.1.min.js','js/select2/pt-BR.js',]    

class SignUpForm(Form):
    nome_usuario = CharField(label='nome_usuario',required=True,validators=[alias_usuario_validator])
    email_alternativo = EmailField(label='email_alternativo',required=True)
    nome = CharField(label='nome',required=True)
    sobrenome = CharField(label='sobrenome',required=True)
    telefone = CharField(label="telefone",required=False)
    vinculo = CharField(label="vinculo",required=False)

    def clean_vinculo(self):
        if self.cleaned_data['vinculo']:
            return self.cleaned_data['vinculo'].lower()
        else:
            None
    
    def clean_telefone(self):
        if self.cleaned_data['telefone'] is self.cleaned_data['telefone'].isnumeric():
            return '+' + self.cleaned_data['telefone']
        elif self.cleaned_data['telefone'] and self.cleaned_data['telefone'][1:len(self.cleaned_data['telefone'])].isnumeric():
            return self.cleaned_data['telefone']
        else:
            return None

class UserSignUpForm(Form):
    teste = CharField(label='teste',widget=TextInput(attrs={':class':"['input',errors.flags.untouched ? '' : errors.flags.valid ? 'is-success' : 'is-danger']"}))