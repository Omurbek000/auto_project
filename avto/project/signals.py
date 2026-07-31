# Сигналы (signals) — «слушатели» событий в Django.
# Когда происходит событие (например, сохранение аренды), Django автоматически
# вызывает эти функции. Здесь мы используем это для двух вещей:
#   1) Автоматически менять доступность машины (is_available) при изменении статуса аренды
#   2) Рассылать уведомления (email + SMS) владельцу и арендатору
#
# Важно: сигналы вызываются и из админки, и из API, поэтому проверки
# статусов дублируют логику views — это сделано намеренно.

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Rental, ChatMessage, Chat
from .services import send_sms

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Rental)
def update_car_availability_on_rental_create(sender, instance, created, **kwargs):
    # Срабатывает ПОСЛЕ создания новой аренды.
    # Задачи: пометить машину недоступной, создать чат для переговоров,
    # уведомить владельца о новой заявке (email + SMS).
    if created and instance.status in ['pending', 'confirmed', 'active']:
        # Пока аренда висит (pending/confirmed/active) — машина занята
        instance.car.is_available = False
        instance.car.save()

        # Чат создаётся автоматически вместе с арендой — сторонам есть где общаться
        Chat.objects.get_or_create(rental=instance)

        # Письмо владельцу о новой заявке на аренду
        if instance.status == 'pending':
            try:
                send_mail(
                    subject=f'Новый запрос на аренду {instance.car.brand} {instance.car.model_name}',
                    message=f'Пользователь {instance.renter.username} хочет арендовать ваш автомобиль с {instance.start_date} по {instance.end_date}.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[instance.car.owner.email],
                    fail_silently=True,
                )
            except Exception as e:
                logger.error('Ошибка email владельцу о новой аренде %s: %s', instance.id, e)

            # SMS-уведомление владельцу (если Twilio настроен — реальное, иначе в консоль)
            try:
                send_sms(
                    instance.car.owner.phone_number,
                    f'Новый запрос на аренду {instance.car.brand} {instance.car.model_name} от {instance.renter.username}'
                )
            except Exception as e:
                logger.error('Ошибка SMS владельцу о новой аренде %s: %s', instance.id, e)


@receiver(pre_save, sender=Rental)
def update_car_availability_on_rental_status_change(sender, instance, **kwargs):
    # Срабатывает ПЕРЕД сохранением изменения существующей аренды.
    # Сравниваем старый статус (из БД) с новым и:
    #   - завершена/отменена аренда  → машина снова доступна
    #   - аренда «оживилась»         → машина снова занята
    #   - pending → confirmed        → письмо и SMS арендатору об подтверждении
    #   - pending → canceled         → письмо и SMS арендатору об отклонении
    if not instance.pk:
        return

    try:
        # Достаём «старую» версию записи, чтобы понять, что именно изменилось
        old_instance = Rental.objects.get(pk=instance.pk)

        # Изменение доступности машины в зависимости от смены статуса
        if old_instance.status in ['pending', 'confirmed', 'active'] and instance.status in ['completed', 'canceled']:
            instance.car.is_available = True
            instance.car.save()
        elif old_instance.status in ['completed', 'canceled'] and instance.status in ['pending', 'confirmed', 'active']:
            instance.car.is_available = False
            instance.car.save()

        # Владелец подтвердил заявку — сообщаем арендатору
        if old_instance.status == 'pending' and instance.status == 'confirmed':
            try:
                send_mail(
                    subject='Ваша аренда подтверждена!',
                    message=f'Владелец подтвердил вашу аренду {instance.car.brand} {instance.car.model_name} с {instance.start_date} по {instance.end_date}.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[instance.renter.email],
                    fail_silently=True,
                )
            except Exception as e:
                logger.error('Ошибка email арендатору о подтверждении %s: %s', instance.id, e)

            try:
                send_sms(
                    instance.renter.phone_number,
                    f'Ваша аренда {instance.car.brand} {instance.car.model_name} подтверждена!'
                )
            except Exception as e:
                logger.error('Ошибка SMS арендатору о подтверждении %s: %s', instance.id, e)

        # Владелец отклонил заявку — сообщаем арендатору
        if old_instance.status == 'pending' and instance.status == 'canceled':
            try:
                send_mail(
                    subject='Ваша аренда отклонена',
                    message=f'К сожалению, владелец отклонил вашу аренду {instance.car.brand} {instance.car.model_name}.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[instance.renter.email],
                    fail_silently=True,
                )
            except Exception as e:
                logger.error('Ошибка email арендатору об отклонении %s: %s', instance.id, e)

            try:
                send_sms(
                    instance.renter.phone_number,
                    f'Ваша аренда {instance.car.brand} {instance.car.model_name} отклонена владельцем'
                )
            except Exception as e:
                logger.error('Ошибка SMS арендатору об отклонении %s: %s', instance.id, e)

    except Rental.DoesNotExist:
        # Бывает при конкурентных сохранениях — просто логируем и пропускаем
        logger.warning('Rental.DoesNotExist в pre_save сигнале для pk=%s', instance.pk)


@receiver(post_save, sender=ChatMessage)
def send_notification_on_new_message(sender, instance, created, **kwargs):
    # Уведомляем собеседника о новом сообщении в чате.
    # Получатель — противоположная сторона аренды:
    # если писал арендатор → уведомляем владельца, и наоборот.
    if not created:
        return

    rental = instance.chat.rental
    # Определяем, кому адресовано уведомление (тот, кто НЕ отправитель)
    recipient = rental.car.owner if instance.sender == rental.renter else rental.renter

    # Письмо получателю (текст сообщения обрезаем до 50 символов для SMS)
    try:
        send_mail(
            subject=f'Новое сообщение от {instance.sender.username}',
            message=f'{instance.sender.username}: {instance.message}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient.email],
            fail_silently=True,
        )
    except Exception as e:
        logger.error('Ошибка email о новом сообщении: %s', e)

    try:
        send_sms(
            recipient.phone_number,
            f'Новое сообщение от {instance.sender.username}: {instance.message[:50]}'
        )
    except Exception as e:
        logger.error('Ошибка SMS о новом сообщении: %s', e)
