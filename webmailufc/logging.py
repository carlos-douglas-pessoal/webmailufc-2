from django.contrib.admin.models import LogEntry

class WebmailUFCLogging:

    @staticmethod
    def log(user,content_type,oid,repr,flag, message = None):        
        LogEntry.objects.log_action(
            user_id = user.id,
            content_type_id = content_type.id,
            object_id = oid,
            object_repr = repr,
            action_flag = flag,
            change_message = f'{content_type.name.capitalize()} adicionada via importação CSV' if not message else message
        )