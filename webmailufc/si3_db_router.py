from redef.models import Discente_SI3,Servidor_SI3,Pessoa_SI3,Usuario_SI3

class SI3DbRouter(object):

    def db_for_read(self, model, **hints):
        if model is Discente_SI3:
            return 'academico'
        elif model is Servidor_SI3:
            return 'administrativo'
        elif model is Pessoa_SI3 or model is Usuario_SI3:
            return 'comum'
        return None
    
    def allow_relation(self, obj1, obj2, **hints):
        return True