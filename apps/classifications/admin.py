from django.contrib import admin
from .models import (
    Category, UserProfile, Classification, GoldStandard, 
    ClassificationSession, SavedAbstract, FollowedDebate, SharedAbstract, SharedDebate,
    AbstractDebate, DebateComment, Notification
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category_type', 'allows_multiple', 'is_active', 'order']
    list_filter = ['category_type', 'is_active', 'allows_multiple']
    search_fields = ['name', 'code', 'description']
    list_editable = ['order', 'is_active']
    ordering = ['category_type', 'order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'category_type', 'description', 'order', 'is_active')
        }),
        ('Behavior', {
            'fields': ('allows_multiple', 'parent')
        }),
        ('Conditional Display', {
            'fields': ('show_if_parent_category', 'show_if_parent_values'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_gold_user', 'reliability_score', 'total_classifications', 
                    'agreement_with_gold', 'completed_training', 'level', 'points']
    list_filter = ['is_gold_user', 'completed_training', 'level']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user', 'is_gold_user')
        }),
        ('Performance Metrics', {
            'fields': ('reliability_score', 'total_classifications', 'agreement_with_gold')
        }),
        ('Training', {
            'fields': ('completed_training', 'training_score', 'training_attempts')
        }),
        ('Gamification', {
            'fields': ('points', 'level', 'badges')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Classification)
class ClassificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'abstract', 'main_classification', 'is_training', 'created_at']
    list_filter = ['main_classification', 'is_training', 'is_valid', 'created_at']
    search_fields = ['user__email', 'abstract__doi', 'abstract__title', 'infrastructure']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Classification', {
            'fields': ('user', 'abstract', 'is_training')
        }),
        ('Answers', {
            'fields': ('main_classification', 'meta_aspects', 'infrastructure', 'comments')
        }),
        ('Metrics', {
            'fields': ('time_spent_seconds',)
        }),
        ('Validation', {
            'fields': ('is_valid', 'validation_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(GoldStandard)
class GoldStandardAdmin(admin.ModelAdmin):
    list_display = ['abstract', 'main_classification', 'main_agreement_score', 
                    'num_gold_classifications', 'updated_at']
    list_filter = ['main_classification', 'main_agreement_score']
    search_fields = ['abstract__doi', 'abstract__title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Abstract', {
            'fields': ('abstract',)
        }),
        ('Main Classification Consensus', {
            'fields': ('main_classification', 'main_agreement_score')
        }),
        ('Meta-research Aspects', {
            'fields': ('meta_aspects', 'meta_agreement_score'),
            'classes': ('collapse',)
        }),
        ('Infrastructure', {
            'fields': ('infrastructure_mentions',),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('num_gold_classifications',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ClassificationSession)
class ClassificationSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'started_at', 'ended_at', 'classifications_count', 'total_time_seconds']
    list_filter = ['started_at']
    search_fields = ['user__email']
    readonly_fields = ['started_at']
    
    fieldsets = (
        ('Session', {
            'fields': ('user', 'started_at', 'ended_at')
        }),
        ('Statistics', {
            'fields': ('classifications_count', 'total_time_seconds')
        }),
    )


@admin.register(SavedAbstract)
class SavedAbstractAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'abstract_preview', 'tag_list', 'saved_at']
    list_filter = ['saved_at']
    search_fields = ['user__email', 'abstract__title', 'notes']
    readonly_fields = ['saved_at', 'updated_at']
    date_hierarchy = 'saved_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'abstract')
        }),
        ('Metadata', {
            'fields': ('notes', 'tags')
        }),
        ('Timestamps', {
            'fields': ('saved_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def abstract_preview(self, obj):
        title = obj.abstract.title
        return title[:50] + '...' if len(title) > 50 else title
    abstract_preview.short_description = 'Abstract'
    abstract_preview.admin_order_field = 'abstract__title'
    
    def tag_list(self, obj):
        return ', '.join(obj.tags) if obj.tags else '-'
    tag_list.short_description = 'Tags'


@admin.register(FollowedDebate)
class FollowedDebateAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'debate_preview', 'followed_at']
    list_filter = ['followed_at']
    search_fields = ['user__email', 'debate__text']
    readonly_fields = ['followed_at']
    date_hierarchy = 'followed_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'debate')
        }),
        ('Timestamps', {
            'fields': ('followed_at',),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def debate_preview(self, obj):
        text = obj.debate.text
        return text[:50] + '...' if len(text) > 50 else text
    debate_preview.short_description = 'Debate'
    debate_preview.admin_order_field = 'debate__text'


@admin.register(SharedAbstract)
class SharedAbstractAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'abstract_preview', 'recipient_email', 'email_sent_successfully', 'shared_at']
    list_filter = ['email_sent_successfully', 'shared_at']
    search_fields = ['user__email', 'user__username', 'recipient_email', 'abstract__title']
    readonly_fields = ['user', 'abstract', 'recipient_email', 'message', 'shared_at', 'email_sent_successfully']
    date_hierarchy = 'shared_at'
    ordering = ['-shared_at']
    
    fieldsets = (
        ('User & Abstract', {
            'fields': ('user', 'abstract')
        }),
        ('Email Details', {
            'fields': ('recipient_email', 'message', 'email_sent_successfully')
        }),
        ('Timestamp', {
            'fields': ('shared_at',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def abstract_preview(self, obj):
        title = obj.abstract.title
        return title[:50] + '...' if len(title) > 50 else title
    abstract_preview.short_description = 'Abstract'
    abstract_preview.admin_order_field = 'abstract__title'
    
    def has_add_permission(self, request):
        # Don't allow manual creation from admin
        return False
    
    def has_change_permission(self, request, obj=None):
        # Don't allow editing
        return False


@admin.register(SharedDebate)
class SharedDebateAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'debate_preview', 'recipient_email', 'email_sent_successfully', 'shared_at']
    list_filter = ['email_sent_successfully', 'shared_at']
    search_fields = ['user__email', 'user__username', 'recipient_email', 'debate__text']
    readonly_fields = ['user', 'debate', 'recipient_email', 'message', 'shared_at', 'email_sent_successfully']
    date_hierarchy = 'shared_at'
    ordering = ['-shared_at']
    
    fieldsets = (
        ('User & Debate', {
            'fields': ('user', 'debate')
        }),
        ('Email Details', {
            'fields': ('recipient_email', 'message', 'email_sent_successfully')
        }),
        ('Timestamp', {
            'fields': ('shared_at',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def debate_preview(self, obj):
        text = obj.debate.text
        return text[:50] + '...' if len(text) > 50 else text
    debate_preview.short_description = 'Debate'
    debate_preview.admin_order_field = 'debate__text'
    
    def has_add_permission(self, request):
        # Don't allow manual creation from admin
        return False
    
    def has_change_permission(self, request, obj=None):
        # Don't allow editing
        return False


@admin.register(AbstractDebate)
class AbstractDebateAdmin(admin.ModelAdmin):
    list_display = ['id', 'text_preview', 'abstract_preview', 'initiator_username', 'created_at', 'is_closed', 'is_pinned', 'views_count', 'comment_count']
    list_filter = ['is_closed', 'is_pinned', 'created_at']
    search_fields = ['text', 'initiator__username', 'initiator__email', 'abstract__title']
    readonly_fields = ['created_at', 'updated_at', 'views_count']
    date_hierarchy = 'created_at'
    ordering = ['-is_pinned', '-created_at']
    
    fieldsets = (
        ('Debate Info', {
            'fields': ('abstract', 'initiator', 'text')
        }),
        ('Status', {
            'fields': ('is_closed', 'is_pinned', 'views_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Text'
    
    def abstract_preview(self, obj):
        title = obj.abstract.title
        return title[:40] + '...' if len(title) > 40 else title
    abstract_preview.short_description = 'Abstract'
    abstract_preview.admin_order_field = 'abstract__title'
    
    def initiator_username(self, obj):
        return obj.initiator.username
    initiator_username.short_description = 'Initiator'
    initiator_username.admin_order_field = 'initiator__username'
    
    def comment_count(self, obj):
        return obj.comments.filter(is_deleted=False).count()
    comment_count.short_description = 'Comments'
    
    actions = ['close_debates', 'reopen_debates', 'pin_debates', 'unpin_debates']
    
    def close_debates(self, request, queryset):
        updated = queryset.update(is_closed=True)
        self.message_user(request, f'{updated} debates closed.')
    close_debates.short_description = 'Close selected debates'
    
    def reopen_debates(self, request, queryset):
        updated = queryset.update(is_closed=False)
        self.message_user(request, f'{updated} debates reopened.')
    reopen_debates.short_description = 'Reopen selected debates'
    
    def pin_debates(self, request, queryset):
        updated = queryset.update(is_pinned=True)
        self.message_user(request, f'{updated} debates pinned.')
    pin_debates.short_description = 'Pin selected debates'
    
    def unpin_debates(self, request, queryset):
        updated = queryset.update(is_pinned=False)
        self.message_user(request, f'{updated} debates unpinned.')
    unpin_debates.short_description = 'Unpin selected debates'


@admin.register(DebateComment)
class DebateCommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'text_preview', 'debate_text_preview', 'user_username', 'created_at', 'is_deleted', 'likes_count']
    list_filter = ['is_deleted', 'created_at']
    search_fields = ['text', 'user__username', 'user__email', 'debate__text']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Comment Info', {
            'fields': ('debate', 'user', 'text')
        }),
        ('Status', {
            'fields': ('is_deleted', 'likes_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def text_preview(self, obj):
        if obj.is_deleted:
            return "[Deleted comment]"
        return obj.text[:60] + '...' if len(obj.text) > 60 else obj.text
    text_preview.short_description = 'Comment'
    
    def debate_text_preview(self, obj):
        text = obj.debate.text
        return text[:40] + '...' if len(text) > 40 else text
    debate_text_preview.short_description = 'Debate'
    debate_text_preview.admin_order_field = 'debate__text'
    
    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = 'User'
    user_username.admin_order_field = 'user__username'
    
    actions = ['soft_delete_comments', 'restore_comments']
    
    def soft_delete_comments(self, request, queryset):
        updated = queryset.update(is_deleted=True)
        self.message_user(request, f'{updated} comments deleted.')
    soft_delete_comments.short_description = 'Delete selected comments (soft delete)'
    
    def restore_comments(self, request, queryset):
        updated = queryset.update(is_deleted=False)
        self.message_user(request, f'{updated} comments restored.')
    restore_comments.short_description = 'Restore selected comments'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_username', 'notification_type', 'actor_username', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'user__email', 'actor__username', 'message']
    readonly_fields = ['created_at', 'read_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Notification Info', {
            'fields': ('user', 'notification_type', 'actor', 'message')
        }),
        ('Related Objects', {
            'fields': ('debate', 'comment')
        }),
        ('Status', {
            'fields': ('is_read', 'read_at')
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = 'User'
    user_username.admin_order_field = 'user__username'
    
    def actor_username(self, obj):
        return obj.actor.username
    actor_username.short_description = 'Actor'
    actor_username.admin_order_field = 'actor__username'
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(is_read=False).update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{updated} notifications marked as read.')
    mark_as_read.short_description = 'Mark selected as read'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.filter(is_read=True).update(is_read=False, read_at=None)
        self.message_user(request, f'{updated} notifications marked as unread.')
    mark_as_unread.short_description = 'Mark selected as unread'
