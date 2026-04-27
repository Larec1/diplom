from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def send_registration_welcome_email(user_email: str) -> None:
    """Письмо после регистрации (выполняется воркером Celery)."""
    send_mail(
        subject=f'Password Reset Token for {user_email}',
        message=(
            f'Подтверждение регистрации для {user_email}.\n'
            f'Регистрация прошла успешно, можно входить через API.'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        fail_silently=False,
    )


@shared_task
def send_order_confirmation_emails(
    order_id: int,
    customer_email: str,
    contact_value: str,
    total: int,
    admin_email: str,
) -> None:
    """Письма покупателю и администратору после подтверждения заказа."""
    from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(
        subject=f'Заказ №{order_id} принят',
        message=(
            f'Здравствуйте!\n\n'
            f'Ваш заказ №{order_id} подтверждён.\n'
            f'Адрес доставки: {contact_value}\n'
            f'Сумма заказа: {total} руб.\n\n'
            f'Спасибо за покупку!'
        ),
        from_email=from_email,
        recipient_list=[customer_email],
        fail_silently=False,
    )
    send_mail(
        subject=f'Новый заказ №{order_id}',
        message=(
            f'Заказ от {customer_email}\n'
            f'Контакт доставки: {contact_value}\n'
            f'Сумма: {total} руб.'
        ),
        from_email=from_email,
        recipient_list=[admin_email],
        fail_silently=False,
    )
