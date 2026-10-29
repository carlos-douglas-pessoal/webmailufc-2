from django.db import models

# Create your models here.

TipoParametroChoices = [
    (0,'Inteiro'),
    (1,'String'),
    (2,'Data'),
    (3,'Lista')
]

class Parametro(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=50,null=False,blank=False,verbose_name="Nome do Parâmetro")
    tipo = models.SmallIntegerField(choices=TipoParametroChoices,null=False,verbose_name="Tipo")
    descricao = models.TextField(verbose_name="Descrição",help_text="Descrição que identifica o parâmetro no sistema")
    valor = models.TextField(null=False,blank=False,verbose_name="Valor",help_text="Valor")

    def __str__(self):
        return self.nome