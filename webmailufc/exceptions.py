class WebmailUFCBaseException(Exception):

    def __init__(self, default_message, message=None):
        msg = default_message if not message else message
        super().__init__(msg)

class LoginException(WebmailUFCBaseException):

    def __init__(self, message=None):
        super().__init__("Usuário ou Senha Inválidos")

class VinculoException(WebmailUFCBaseException):

    def __init__(self, message=None):
        super().__init__("Usuário sem vínculo com a instituição", message)

class UsuarioJaExisteException(WebmailUFCBaseException):

    def __init__(self, email,):
        super().__init__(f"Este email {email} já existe")

class FormularioCadastroException(WebmailUFCBaseException):

    def __init__(self):
        super().__init__("Um ou mais campos do formulário estão incorretos")