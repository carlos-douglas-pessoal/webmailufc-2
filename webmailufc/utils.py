from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from parameters.models import Parametro

import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

webmailufc_email = 'webmailufc-noreply@ufc.br'


def enviar_senha(primary,alternative,password,is_new, nome=None):
    server = smtplib.SMTP('smtp.ufc.br',25)
    server.ehlo()
    server.starttls()
    server.ehlo()
    telefone_sti = Parametro.objects.filter(nome='TELEFONE_STI').first() or '-'
    html_content = render_to_string('email.html', {'email':primary,'password':password, 'is_new': is_new, 'telefone': telefone_sti.valor, 'nome': nome})
    # text_content = strip_tags(html_content)
    title = '[WebmailUFC] '
    if is_new:
        title += 'Criação de Email'
    else:
        title += 'Redefinição de senha'

    msg = MIMEMultipart('alternative')
    msg['Subject'] = title
    msg['From'] = webmailufc_email
    msg['To'] = alternative

    text = MIMEText(html_content, 'html')
    msg.attach(text)

    server.send_message(msg)
    server.quit()








# def enviar_senha(primary,alternative, password, is_new):
#     html_content = render_to_string('email.html', {'email':primary,'password':password, 'is_new': is_new})
#     text_content = strip_tags(html_content)
#     title = '[WebmailUFC] '
#     if is_new:
#         title += 'Criação de Email'
#     else:
#         title += 'Redefinição de senha'
#     msg = EmailMultiAlternatives(title, text_content, "webmailufc@ufc.br", [alternative])
#     msg.attach_alternative(html_content, "text/html")
#     msg.send()
