from django.db import models
from django.contrib.auth import get_user_model
from django_countries.fields import CountryField
from apps.abstracts.models import Abstract

User = get_user_model()


class Category(models.Model):
    """Hierarchical categories for classification"""
    CATEGORY_TYPES = [
        ('main', 'Main Classification'),
        ('meta_aspect', 'Meta-research Aspect'),
    ]
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=100, unique=True, db_index=True)
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES, db_index=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    allows_multiple = models.BooleanField(default=False)
    
    # Conditional logic
    show_if_parent_category = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='conditional_children'
    )
    show_if_parent_values = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['category_type', 'order', 'name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['category_type', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.get_category_type_display()}: {self.name}"


class UserProfile(models.Model):
    """User profile extension"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='classification_profile')
    
    # User classification
    is_gold_user = models.BooleanField(default=False)
    reliability_score = models.FloatField(default=0.0)
    total_classifications = models.IntegerField(default=0)
    agreement_with_gold = models.FloatField(default=0.0)
    
    # Onboarding
    completed_training = models.BooleanField(default=False)
    training_score = models.FloatField(default=0.0)
    training_attempts = models.IntegerField(default=0)
    
    # Gamification
    points = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    badges = models.JSONField(default=list)
    
    # Profile information (optional)
    first_name = models.CharField(
        max_length=150,
        blank=True,
        default='',
        help_text="User's first name (optional)"
    )
    last_name = models.CharField(
        max_length=150,
        blank=True,
        default='',
        help_text="User's last name (optional)"
    )
    country = CountryField(
        blank=True,
        blank_label='(select country)',
        help_text="User's country (optional, ISO 3166)"
    )
    institution = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="User's institution or affiliation (optional)"
    )
    is_profile_public = models.BooleanField(
        default=False,
        help_text="Whether to show profile in public leaderboards and stats"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def get_display_name(self):
        """
        Return user's full name if available, otherwise email
        """
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.user.email
    
    def __str__(self):
        return f"{self.user.email} - {'Gold' if self.is_gold_user else 'Regular'} (Score: {self.reliability_score:.1f})"


class Classification(models.Model):
    """Individual classification of an abstract by a user"""
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='user_classifications',
        help_text="User who made the classification. Can be null if user is deleted but classifications are preserved."
    )
    abstract = models.ForeignKey(Abstract, on_delete=models.CASCADE, related_name='classifications')
    
    # Main classification (required) - stores the category code
    main_classification = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Code of the main classification category"
    )
    
    # Meta-research aspects (only if main_classification = 'meta_research')
    meta_aspects = models.JSONField(default=list, blank=True, help_text="List of meta-research aspect codes")
    
    # Infrastructure mentioned (optional, free text)
    infrastructure = models.TextField(blank=True, max_length=500, help_text="Infrastructure or tools mentioned")
    
    # Additional info
    comments = models.TextField(blank=True)
    
    # Metrics
    time_spent_seconds = models.IntegerField(default=0)
    is_training = models.BooleanField(default=False)
    
    # Validation
    is_valid = models.BooleanField(default=True)
    validation_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'abstract']
        ordering = ['-created_at']
        verbose_name = 'Classification'
        verbose_name_plural = 'Classifications'
        indexes = [
            models.Index(fields=['user', 'abstract']),
            models.Index(fields=['main_classification']),
            models.Index(fields=['is_training']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        abstract_id = self.abstract.doi if self.abstract.doi else f"ID:{self.abstract.id}"
        return f"{self.user.email} → {abstract_id} ({self.main_classification})"
    
    def get_main_category(self):
        """Get the Category object for this classification's main_classification"""
        try:
            return Category.objects.get(code=self.main_classification, category_type='main')
        except Category.DoesNotExist:
            return None


class GoldStandard(models.Model):
    """Consensus classifications from gold users"""
    abstract = models.ForeignKey(Abstract, on_delete=models.CASCADE, related_name='gold_standards')
    
    # Main classification consensus
    main_classification = models.CharField(max_length=50)
    main_agreement_score = models.FloatField(help_text="Agreement level (0-1)")
    
    # Meta aspects consensus (if applicable)
    meta_aspects = models.JSONField(default=list, blank=True)
    meta_agreement_score = models.FloatField(default=0.0)
    
    # Infrastructure mentions
    infrastructure_mentions = models.JSONField(default=list, blank=True, help_text="List of infrastructure mentions")
    
    num_gold_classifications = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Gold Standard'
        verbose_name_plural = 'Gold Standards'
    
    def __str__(self):
        return f"Gold: {self.abstract.doi} - {self.main_classification}"


class ClassificationSession(models.Model):
    """User classification session"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='classification_sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    classifications_count = models.IntegerField(default=0)
    total_time_seconds = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Classification Session'
        verbose_name_plural = 'Classification Sessions'
    
    def __str__(self):
        return f"{self.user.email} - {self.started_at.strftime('%Y-%m-%d %H:%M')}"


class SavedAbstract(models.Model):
    """
    Model to save/bookmark abstracts for later reference
    Users can save interesting abstracts to their personal library
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='saved_abstracts'
    )
    abstract = models.ForeignKey(
        'abstracts.Abstract',
        on_delete=models.CASCADE,
        related_name='saved_by_users'
    )
    
    # Optional metadata
    notes = models.TextField(
        blank=True,
        help_text="Personal notes about this abstract"
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Personal tags/labels for organization"
    )
    
    # Timestamps
    saved_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'abstract']
        ordering = ['-saved_at']
        verbose_name = 'Saved Abstract'
        verbose_name_plural = 'Saved Abstracts'
        indexes = [
            models.Index(fields=['user', '-saved_at']),
            models.Index(fields=['abstract']),
        ]
    
    def __str__(self):
        title_preview = self.abstract.title[:50] if self.abstract.title else 'Untitled'
        return f"{self.user.email} saved '{title_preview}'"


class FollowedDebate(models.Model):
    """
    Model to follow debates for updates
    Users can follow debates to stay updated on new comments
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='followed_debates'
    )
    debate = models.ForeignKey(
        'AbstractDebate',
        on_delete=models.CASCADE,
        related_name='followed_by_users'
    )
    
    # Timestamps
    followed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'debate']
        ordering = ['-followed_at']
        verbose_name = 'Followed Debate'
        verbose_name_plural = 'Followed Debates'
        indexes = [
            models.Index(fields=['user', '-followed_at']),
            models.Index(fields=['debate']),
        ]
    
    def __str__(self):
        text_preview = self.debate.text[:50] if self.debate.text else 'No text'
        return f"{self.user.email} follows debate '{text_preview}'"


class SharedAbstract(models.Model):
    """
    Model to track when users share abstracts via email
    Keeps history of shared abstracts for statistics
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shared_abstracts'
    )
    abstract = models.ForeignKey(
        'abstracts.Abstract',
        on_delete=models.CASCADE,
        related_name='shared_by_users'
    )
    
    # Email details
    recipient_email = models.EmailField(
        help_text="Email address of the recipient"
    )
    message = models.TextField(
        blank=True,
        help_text="Personal message from sender"
    )
    
    # Tracking
    shared_at = models.DateTimeField(auto_now_add=True)
    email_sent_successfully = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-shared_at']
        verbose_name = 'Shared Abstract'
        verbose_name_plural = 'Shared Abstracts'
        indexes = [
            models.Index(fields=['user', '-shared_at']),
            models.Index(fields=['abstract', '-shared_at']),
        ]
    
    def __str__(self):
        title_preview = self.abstract.title[:50] if self.abstract.title else 'Untitled'
        return f"{self.user.email} shared '{title_preview}' to {self.recipient_email}"


class SharedDebate(models.Model):
    """
    Model to track when users share debates via email
    Keeps history of shared debates for statistics
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shared_debates'
    )
    debate = models.ForeignKey(
        'AbstractDebate',
        on_delete=models.CASCADE,
        related_name='shared_by_users'
    )
    
    # Email details
    recipient_email = models.EmailField(
        help_text="Email address of the recipient"
    )
    message = models.TextField(
        blank=True,
        help_text="Personal message from sender"
    )
    
    # Tracking
    shared_at = models.DateTimeField(auto_now_add=True)
    email_sent_successfully = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-shared_at']
        verbose_name = 'Shared Debate'
        verbose_name_plural = 'Shared Debates'
        indexes = [
            models.Index(fields=['user', '-shared_at']),
            models.Index(fields=['debate', '-shared_at']),
        ]
    
    def __str__(self):
        text_preview = self.debate.text[:50] if self.debate.text else 'No text'
        return f"{self.user.email} shared debate '{text_preview}' to {self.recipient_email}"


class AbstractDebate(models.Model):
    """
    Debate thread on an abstract for academic discussion
    Multiple users can discuss different aspects of a research paper
    """
    abstract = models.ForeignKey(
        'abstracts.Abstract',
        on_delete=models.CASCADE,
        related_name='debates'
    )
    initiator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='initiated_debates'
    )
    
    # Debate content
    text = models.TextField(
        help_text="Initial post explaining the debate topic"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_closed = models.BooleanField(
        default=False,
        help_text="Closed debates don't accept new comments"
    )
    is_pinned = models.BooleanField(
        default=False,
        help_text="Pinned debates appear at the top"
    )
    views_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
        verbose_name = 'Abstract Debate'
        verbose_name_plural = 'Abstract Debates'
        indexes = [
            models.Index(fields=['abstract', '-created_at']),
            models.Index(fields=['initiator', '-created_at']),
            models.Index(fields=['-is_pinned', '-created_at']),
        ]
    
    def __str__(self):
        text_preview = self.text[:50] if len(self.text) > 50 else self.text
        return f"Debate: {text_preview} on {self.abstract.title[:30]}"
    
    @property
    def comments_count(self):
        """Count active (non-deleted) comments"""
        return self.comments.filter(is_deleted=False).count()


class DebateComment(models.Model):
    """
    Comment in a debate thread (flat comments, no nesting)
    Like X/Twitter: no editing, only delete
    """
    debate = models.ForeignKey(
        AbstractDebate,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='debate_comments'
    )
    
    # Comment content
    text = models.TextField(
        max_length=350,
        help_text="Comment text (max 350 characters)"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(
        default=False,
        help_text="Soft delete: shows 'Comment deleted' instead of text"
    )
    likes_count = models.IntegerField(
        default=0,
        help_text="Number of likes (for future implementation)"
    )
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Debate Comment'
        verbose_name_plural = 'Debate Comments'
        indexes = [
            models.Index(fields=['debate', 'created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        if self.is_deleted:
            return f"[Deleted comment] by {self.user.username}"
        text_preview = self.text[:50] if len(self.text) > 50 else self.text
        return f"{self.user.username}: {text_preview}"


class Notification(models.Model):
    """
    User notifications for debate interactions
    """
    NOTIFICATION_TYPES = [
        ('debate_comment', 'New comment on your debate'),
        ('debate_reply', 'Reply to your comment'),
        ('debate_mention', 'Mentioned in a comment'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="User who receives this notification"
    )
    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES,
        db_index=True
    )
    
    # Related objects
    debate = models.ForeignKey(
        AbstractDebate,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    comment = models.ForeignKey(
        DebateComment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    actor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='triggered_notifications',
        help_text="User who triggered this notification (e.g., who commented)"
    )
    
    # Notification content
    message = models.TextField(help_text="Notification message")
    
    # Status
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['notification_type', '-created_at']),
        ]
    
    def __str__(self):
        status = "Read" if self.is_read else "Unread"
        return f"[{status}] {self.get_notification_type_display()} for {self.user.username}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
