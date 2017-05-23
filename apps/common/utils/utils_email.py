# coding=UTF-8
'''
邮件处理工具类
Created on 2011-09-07
@author: zhangyu
'''

# from socket import error as socket_error
# from django.core.mail import SMTPConnection, EmailMessage

from django.core.mail import send_mail


"""
usage:

send_mail(subject, message, from_email, recipient_list, fail_silently=False, auth_user=None, auth_password=None, connection=None, html_message=None)

如果html_message不为空，则使用html_message，否则使用message

"""

send_html_email = send_mail

# def send_html_email(subject, content, from_email, to_email, filepath_list = [], content_subtype = "html", connection = None):
#     try:
#         if not connection:
#             connection = SMTPConnection()
#         msg = EmailMessage(subject, content, from_email, to_email, connection = connection)
#         if filepath_list:
#             for filepath in filepath_list:
#                 msg.attach_file(filepath)
#         msg.content_subtype = content_subtype # Main content is now text/html
#         return msg.send()
#     except (socket_error, smtplib.SMTPSenderRefused, smtplib.SMTPRecipientsRefused), e:
#         log.exception("to_email=%s, e=%s" % (to_email, e))
#     except smtplib.SMTPAuthenticationError, e:
#         log.exception("to_email=%s, e=(%s, %s)" % (to_email, e.smtp_code, e.smtp_error.decode('gb2312').encode('utf-8')))
#     except Exception, e:
#         log.exception("to_email=%s, e=%s" % (to_email, e))
#     return False
