from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
import logging
import uuid

logger = logging.getLogger(__name__)


class CustomAccountAdapter(DefaultAccountAdapter):
    """Custom account adapter to customize email confirmation URLs for frontend"""
    
    def generate_unique_username(self, txts, regex=None):
        """
        Generate a unique username from email
        Creates a username like: user_abc123de
        """
        # Get the base from email (part before @)
        base_username = txts[0].split('@')[0] if txts else 'user'
        
        # Clean the username (remove special characters, keep only alphanumeric and underscore)
        base_username = ''.join(c if c.isalnum() or c == '_' else '_' for c in base_username)
        
        # Limit to 20 characters to leave room for suffix
        base_username = base_username[:20]
        
        # Add a unique suffix
        unique_suffix = uuid.uuid4().hex[:8]
        username = f"{base_username}_{unique_suffix}"
        
        return username
    
    def format_email_subject(self, subject):
        """
        Override to remove the automatic [sitename] prefix
        Just return the subject as-is from the template
        """
        return subject
    
    def send_confirmation_mail(self, request, emailconfirmation, signup):
        """Override to use frontend URL for email confirmation"""
        try:
            logger.info(f"=== Starting email confirmation process ===")
            logger.info(f"User: {emailconfirmation.email_address.user.username}")
            logger.info(f"Email: {emailconfirmation.email_address.email}")
            logger.info(f"Key: {emailconfirmation.key}")
            
            # Create the frontend confirmation URL
            activate_url = f"{settings.FRONTEND_URL}/verify-email/{emailconfirmation.key}"
            logger.info(f"Activation URL: {activate_url}")
            
            # Get user's display name (full name or email)
            user = emailconfirmation.email_address.user
            try:
                profile = user.classification_profile
                display_name = profile.get_display_name()
            except:
                display_name = user.email
            
            ctx = {
                "user": user,
                "display_name": display_name,
                "activate_url": activate_url,
                "current_site": settings.SITE_NAME,
                "key": emailconfirmation.key,
            }
            
            logger.info(f"Email context: {ctx}")
            logger.info(f"SITE_NAME: {settings.SITE_NAME}")
            logger.info(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
            logger.info(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
            
            # Use our custom email templates
            email_template = 'emails/verification/email_confirmation'
            logger.info(f"Using email template: {email_template}")
            
            result = self.send_mail(email_template, emailconfirmation.email_address.email, ctx)
            logger.info(f"Email send result: {result}")
            logger.info(f"=== Email confirmation process completed ===")
            
            return result
            
        except Exception as e:
            logger.error(f"=== ERROR sending confirmation email ===")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            logger.exception("Full traceback:")
            raise
