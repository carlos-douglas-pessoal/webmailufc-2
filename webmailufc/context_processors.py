from django.conf import settings

def from_settings(request):
    return {
        'DEBUG': settings.DEBUG,
        'ENVIRONMENT_NAME': settings.ENVIRONMENT_NAME,
        'ENVIRONMENT_COLOR': settings.ENVIRONMENT_COLOR,
    }