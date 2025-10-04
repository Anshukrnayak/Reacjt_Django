from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings



@shared_task
def send_email_task(subject, message, recipient_list, from_email=None):
    """
    Celery task to send email asynchronously
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL

    try:
        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=False,
        )
        return f"Email sent successfully to {recipient_list}"
    except Exception as e:
        return f"Failed to send email: {str(e)}"

@shared_task
def send_welcome_email(user_email, username):
    """
    Example: Send welcome email to new users
    """
    subject = 'Welcome to Our Service!'
    message = f'''
    Hello {username},
    
    Welcome to our service! We're excited to have you on board.
    
    Best regards,
    The Team
    '''

    return send_email_task.delay(subject, message, [user_email])

