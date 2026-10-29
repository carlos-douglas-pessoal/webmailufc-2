class HttpResponseMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        if view_func.__name__ == 'LoginView':
            request.titulo = 'Login'
        elif view_func.__name__ == 'RedefineView':
            request.titulo = 'Redefinir dados pessoais'
        elif view_func.__name__ == 'SignUpView':
            request.titulo = 'Criar conta'
        elif view_func.__name__ == 'SuccessView':
            request.titulo = 'A conta foi criada!'
        elif view_func.__name__ == 'VinculoView':
            request.titulo = 'Seleção de vínculos'
        response = view_func(request, *view_args, **view_kwargs)
        return response