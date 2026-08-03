# Вспомогательные сервисы — отправка email и SMS
# В dev-режиме выводят в консоль. В production отправляют по-настоящему

from django.conf import settings
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)


# Отправка email. Если SMTP не настроен — выводит в консоль
def send_email(subject, message, recipient_list):
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.warning(f'[EMAIL] Ошибка отправки на {recipient_list}: {e}')
        print(f'[EMAIL] To: {recipient_list} | Subject: {subject} | Message: {message}')
        return False


# Запись действия в журнал аудита (AuditLog).
# Вызывается из views при важных событиях: регистрация, блокировка/верификация
# пользователя, смена ролей, изменение статуса жалобы, ответ админа.
# Аргументы:
#   user    — кто совершил действие (может быть None)
#   action  — строковый код действия, например 'user.blocked'
#   obj     — объект, над которым совершено действие (необязательно)
#   details — словарь с доп. информацией (например {'from': 'pending', 'to': 'resolved'})
def log_action(user, action, obj=None, details=None):
    from .models import AuditLog  # локальный импорт — чтобы не было циклической зависимости

    return AuditLog.objects.create(
        user=user,
        action=action,
        model_name=obj.__class__.__name__ if obj else '',
        object_id=obj.pk if obj else None,
        details=details or {},
    )


# Отправка SMS. Если Twilio не настроен — выводит в консоль
def send_sms(phone_number, message):
    if not phone_number:
        print(f'[SMS] Нет номера телефона. Сообщение: {message}')
        return False

    twilio_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
    twilio_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
    twilio_phone = getattr(settings, 'TWILIO_PHONE_NUMBER', None)

    if twilio_sid and twilio_token and twilio_phone:
        try:
            from twilio.rest import Client
            client = Client(twilio_sid, twilio_token)
            client.messages.create(
                body=message,
                from_=twilio_phone,
                to=phone_number
            )
            return True
        except Exception as e:
            logger.warning(f'[SMS] Twilio ошибка: {e}')

    # Если Twilio не настроен — выводим в консоль
    print(f'[SMS] To: {phone_number} | Message: {message}')
    return False
