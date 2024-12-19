import secrets
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

def generate_otp(length=6):
    """
    Generate a secure random OTP of specified length
    """
    return ''.join(secrets.choice('0123456789') for _ in range(length))

def send_otp_email(user, otp):
    """
    Send OTP to user's email
    """
    subject = 'Your Account Verification OTP'
    message = f'''
    Dear {user.full_name},

    Your account verification OTP is: {otp}

    This OTP is valid for 4 minutes. Do not share it with anyone.

    Best regards,
    Your Application Team
    '''
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except Exception as e:
        # Log the error (you can replace this with proper logging)
        print(f"Error sending email: {e}")

