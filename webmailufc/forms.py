
from django.forms import *
from .models import *

class ContasCSVForm(ModelForm):

    csv = FileField(label='Arquivo CSV',allow_empty_file=False,required=True,help_text='Arquivo CSV no formato "id,cpf,email_ufc,data_cadastro"',widget=FileInput())
    cadastrado_em = CharField(label="Cadastrado em",required=False,widget=TextInput())


    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(ContasCSVForm, self).__init__(*args, **kwargs)
        if self.instance and not self.instance.pk:
            self.fields['cadastrado_por'].widget = HiddenInput()
            self.initial['cadastrado_por'] = self.request.user
            self.fields['cadastrado_em'].widget = HiddenInput()            
        elif self.instance:  
            self.instance.cadastrado_em = self.instance.data_cadastro.strftime("%d/%m/%Y (%H:%M)")
    
    def save(self,commit=True):        
        return super().save(commit)

    class Meta:
        exclude = ('id','data_cadastro',)
        model = ImportacaoContas
        fields = ['csv','cadastrado_por']    