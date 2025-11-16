from django import forms
from django.contrib.auth.forms import PasswordResetForm as DjangoPasswordResetForm
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from allauth.account.forms import default_token_generator as allauth_token_generator
from allauth.account.utils import user_pk_to_url_str


class CustomPasswordResetForm(DjangoPasswordResetForm):
    """
    Custom password reset form to use frontend URL
    """
    def save(self, domain_override=None, subject_template_name='emails/password_reset/password_reset_subject.txt',
             email_template_name='emails/password_reset/password_reset_message.txt',
             use_https=False, token_generator=allauth_token_generator,
             from_email=None, request=None, html_email_template_name='emails/password_reset/password_reset_message.html',
             extra_email_context=None):
        """
        Generate a one-use only link for resetting password and send it to the user.
        """
        email = self.cleaned_data["email"]
        if not domain_override:
            domain_override = settings.SITE_NAME
        
        for user in self.get_users(email):
            # Use allauth's base36 encoder since we have allauth installed
            uid = user_pk_to_url_str(user)
            token = token_generator.make_token(user)
            
            # Create frontend reset URL
            password_reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"
            
            # Get user's display name (full name or email)
            try:
                profile = user.classification_profile
                display_name = profile.get_display_name()
            except:
                display_name = user.email
            
            context = {
                'email': email,
                'domain': domain_override,
                'site_name': settings.SITE_NAME,
                'uid': uid,
                'user': user,
                'display_name': display_name,
                'token': token,
                'password_reset_url': password_reset_url,
                'protocol': 'https' if use_https else 'http',
            }
            if extra_email_context is not None:
                context.update(extra_email_context)
            
            self.send_mail(
                subject_template_name, email_template_name, context, from_email,
                email, html_email_template_name=html_email_template_name,
            )
