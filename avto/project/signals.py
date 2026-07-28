from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Rental, ChatMessage, Chat
from django.core.mail import send_mail
from django.conf import settings


@receiver(post_save, sender=Rental)
def update_car_availability_on_rental_create(sender, instance, created, **kwargs):
    if created and instance.status in ['pending', 'confirmed', 'active']:
        instance.car.is_available = False
        instance.car.save()

        # Создать чат для аренды
        Chat.objects.get_or_create(rental=instance)

        # Уведомление владельцу о новом запросе
        if created and instance.status == 'pending':
            try:
                send_mail(
                    subject=f'Новый запрос на аренду {instance.car.brand} {instance.car.model_name}',
                    message=f'Пользователь {instance.renter.username} хочет арендовать ваш автомобиль с {instance.start_date} по {instance.end_date}.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[instance.car.owner.email],
                    fail_silently=True,
                )
            except:
                pass


@receiver(pre_save, sender=Rental)
def update_car_availability_on_rental_status_change(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Rental.objects.get(pk=instance.pk)

            if old_instance.status in ['pending', 'confirmed', 'active'] and instance.status in ['completed', 'canceled']:
                instance.car.is_available = True
                instance.car.save()

            elif old_instance.status in ['completed', 'canceled'] and instance.status in ['pending', 'confirmed', 'active']:
                instance.car.is_available = False
                instance.car.save()

            # Уведомление о подтверждении аренды
            if old_instance.status == 'pending' and instance.status == 'confirmed':
                try:
                    send_mail(
                        subject=f'Ваша аренда подтверждена!',
                        message=f'Владелец подтвердил вашу аренду {instance.car.brand} {instance.car.model_name} с {instance.start_date} по {instance.end_date}.',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[instance.renter.email],
                        fail_silently=True,
                    )
                except:
                    pass

            # Уведомление об отклонении
            if old_instance.status == 'pending' and instance.status == 'canceled':
                try:
                    send_mail(
                        subject=f'Ваша аренда отклонена',
                        message=f'К сожалению, владелец отклонил вашу аренду {instance.car.brand} {instance.car.model_name}.',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[instance.renter.email],
                        fail_silently=True,
                    )
                except:
                    pass

        except Rental.DoesNotExist:
            pass


@receiver(post_save, sender=ChatMessage)
def send_notification_on_new_message(sender, instance, created, **kwargs):
    if created:
        rental = instance.chat.rental

        # Определить получателя (не отправителя)
        if instance.sender == rental.renter:
            recipient = rental.car.owner
        else:
            recipient = rental.renter

        try:
            send_mail(
                subject=f'Новое сообщение от {instance.sender.username}',
                message=f'{instance.sender.username}: {instance.message}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=True,
            )
        except:
            pass
