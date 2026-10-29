from django.apps import AppConfig


class ParametersConfig(AppConfig):
    name = 'parameters'
    verbose_name = 'Parâmetros do Sistema'

    def __init__(self, app_name, app_module):
        super(ParametersConfig, self).__init__(app_name, app_module)
