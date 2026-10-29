from django.apps import AppConfig


class RedefConfig(AppConfig):
    name = 'redef'
    verbose_name = 'Gerenciamento de Contas'

    def __init__(self, app_name, app_module):
        super(RedefConfig, self).__init__(app_name, app_module)
