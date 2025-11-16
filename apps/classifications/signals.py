from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Classification, UserProfile, DebateComment, Notification
from apps.abstracts.models import Abstract

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create UserProfile when a new user is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when user is saved"""
    if hasattr(instance, 'classification_profile'):
        instance.classification_profile.save()


@receiver(post_save, sender=Classification)
def update_classification_counts(sender, instance, created, **kwargs):
    """Update counts when a classification is created"""
    if created:
        # Update abstract classification count
        abstract = instance.abstract
        abstract.current_classifications_count = abstract.classifications.filter(is_valid=True).count()
        
        # Check if consensus is reached
        if abstract.current_classifications_count >= abstract.required_classifications:
            abstract.consensus_reached = True
        
        abstract.save()
        
        # Update user profile total classifications
        profile = instance.user.classification_profile
        profile.total_classifications = instance.user.user_classifications.filter(is_valid=True).count()
        profile.save()


@receiver(post_save, sender=DebateComment)
def create_debate_comment_notification(sender, instance, created, **kwargs):
    """
    Create notification when someone comments on a debate
    Notifies the debate initiator (unless they're the one commenting)
    """
    if not created:
        return
    
    comment = instance
    debate = comment.debate
    
    # Don't notify if the commenter is the debate initiator
    if comment.user == debate.initiator:
        return
    
    # Create notification for debate initiator
    abstract_title = debate.abstract.title[:50]
    if len(debate.abstract.title) > 50:
        abstract_title += "..."
    
    Notification.objects.create(
        user=debate.initiator,
        notification_type='debate_comment',
        debate=debate,
        comment=comment,
        actor=comment.user,
        message=f"{comment.user.username} commented on your debate about \"{abstract_title}\""
    )
