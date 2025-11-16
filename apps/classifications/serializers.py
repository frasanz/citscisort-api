from rest_framework import serializers
from django.contrib.auth import get_user_model
from django_countries.serializers import CountryFieldMixin
from .models import (
    Category, UserProfile, Classification, GoldStandard, 
    ClassificationSession, SavedAbstract, FollowedDebate, SharedAbstract,
    AbstractDebate, DebateComment, Notification
)
from apps.abstracts.serializers import AbstractListSerializer

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    children = serializers.SerializerMethodField()
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'code', 'category_type', 'parent', 'parent_name',
            'description', 'order', 'is_active', 'allows_multiple',
            'show_if_parent_category', 'show_if_parent_values', 'children'
        ]
    
    def get_children(self, obj):
        if obj.children.exists():
            return CategorySerializer(obj.children.filter(is_active=True), many=True).data
        return []


class CategoryListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for category lists"""
    
    class Meta:
        model = Category
        fields = ['id', 'code', 'name', 'category_type', 'description', 'allows_multiple', 'order']


class UserProfileSerializer(CountryFieldMixin, serializers.ModelSerializer):
    """Serializer for UserProfile model"""
    email = serializers.EmailField(source='user.email', read_only=True)
    display_name = serializers.CharField(source='get_display_name', read_only=True)
    preferred_areas = CategoryListSerializer(many=True, read_only=True)
    country_name = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'email', 'display_name', 'first_name', 'last_name', 'is_gold_user',
            'reliability_score', 'total_classifications', 'agreement_with_gold',
            'completed_training', 'training_score', 'training_attempts',
            'points', 'level', 'badges', 'preferred_areas',
            'country', 'country_name', 'institution', 'is_profile_public'
        ]
        read_only_fields = [
            'reliability_score', 'total_classifications', 'agreement_with_gold',
            'training_score', 'points', 'level', 'badges', 'country_name', 'display_name'
        ]
    
    def get_country_name(self, obj):
        """Get human-readable country name"""
        return obj.country.name if obj.country else None


class UserProfileUpdateSerializer(CountryFieldMixin, serializers.ModelSerializer):
    """Serializer for updating user profile - only editable fields"""
    
    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'country', 'institution', 'is_profile_public']
    
    def to_representation(self, instance):
        """Return full profile data after update"""
        return UserProfileSerializer(instance).data


class PublicUserProfileSerializer(CountryFieldMixin, serializers.ModelSerializer):
    """Serializer for public profiles - no email, conditional display"""
    display_name = serializers.SerializerMethodField()
    country_name = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'display_name', 'country', 'country_name', 'institution',
            'total_classifications', 'level', 'points', 'badges'
        ]
    
    def get_display_name(self, obj):
        """Show name if profile is public and name exists, otherwise anonymize"""
        if obj.is_profile_public:
            return obj.get_display_name()
        return f"User{obj.user.id % 1000}"
    
    def get_country_name(self, obj):
        """Get human-readable country name"""
        return obj.country.name if obj.country else None


class ClassificationSerializer(serializers.ModelSerializer):
    """Serializer for Classification model"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    abstract_info = AbstractListSerializer(source='abstract', read_only=True)
    
    class Meta:
        model = Classification
        fields = [
            'id', 'user', 'user_email', 'abstract', 'abstract_info',
            'main_classification', 'meta_aspects', 'infrastructure',
            'comments', 'time_spent_seconds', 'is_training', 'is_valid',
            'validation_notes', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'is_valid', 'validation_notes']


class ClassificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating classifications"""
    
    class Meta:
        model = Classification
        fields = [
            'abstract', 'main_classification', 'meta_aspects', 
            'infrastructure', 'comments', 'time_spent_seconds'
        ]
    
    def to_internal_value(self, data):
        """Convert meta_aspects to list if it's a string"""
        # Make a mutable copy
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        
        # Handle meta_aspects - ensure it's a list
        if 'meta_aspects' in data:
            meta_aspects = data['meta_aspects']
            
            # If it's a string, try to parse it
            if isinstance(meta_aspects, str):
                import json
                
                # First, try to parse as JSON array
                try:
                    parsed = json.loads(meta_aspects)
                    if isinstance(parsed, list):
                        data['meta_aspects'] = parsed
                    else:
                        # If it's not a list, convert to list with single element
                        data['meta_aspects'] = [parsed] if parsed else []
                except json.JSONDecodeError:
                    # If not valid JSON, check if it's comma-separated values
                    if ',' in meta_aspects:
                        # Split by comma and strip whitespace from each value
                        data['meta_aspects'] = [
                            code.strip() 
                            for code in meta_aspects.split(',') 
                            if code.strip()
                        ]
                    else:
                        # Single value, not comma-separated
                        data['meta_aspects'] = [meta_aspects.strip()] if meta_aspects.strip() else []
            elif not isinstance(meta_aspects, list):
                # If it's not a list or string, convert to list
                data['meta_aspects'] = [meta_aspects] if meta_aspects else []
        else:
            # Default to empty list if not provided
            data['meta_aspects'] = []
        
        return super().to_internal_value(data)
    
    def validate(self, attrs):
        """Validate the classification data"""
        main_classification = attrs.get('main_classification')
        meta_aspects = attrs.get('meta_aspects', [])
        
        # Validate that main_classification code exists
        if not Category.objects.filter(
            code=main_classification, 
            category_type='main', 
            is_active=True
        ).exists():
            raise serializers.ValidationError({
                'main_classification': f'Invalid category code: {main_classification}'
            })
        
        # Check if main classification is meta_research
        is_meta_research = main_classification == 'main_meta_research'
        
        # If main classification is meta_research, meta_aspects should be provided
        if is_meta_research and not meta_aspects:
            raise serializers.ValidationError({
                'meta_aspects': 'Meta-research aspects are required when main classification is meta-research'
            })
        
        # If main classification is NOT meta_research, meta_aspects should be empty
        if not is_meta_research and meta_aspects:
            raise serializers.ValidationError({
                'meta_aspects': 'Meta-research aspects can only be selected when main classification is meta-research'
            })
        
        # Validate that all meta aspect codes exist
        if meta_aspects:
            valid_codes = set(Category.objects.filter(
                category_type='meta_aspect',
                is_active=True
            ).values_list('code', flat=True))
            
            invalid_codes = set(meta_aspects) - valid_codes
            if invalid_codes:
                raise serializers.ValidationError({
                    'meta_aspects': f'Invalid meta-aspect codes: {", ".join(invalid_codes)}'
                })
        
        return attrs
    
    def create(self, validated_data):
        """Create classification with user from request context"""
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


class GoldStandardSerializer(serializers.ModelSerializer):
    """Serializer for GoldStandard model"""
    abstract_doi = serializers.CharField(source='abstract.doi', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = GoldStandard
        fields = [
            'id', 'abstract', 'abstract_doi', 'category', 'category_name',
            'consensus_value', 'agreement_score', 'num_gold_classifications',
            'created_at', 'updated_at'
        ]


class ClassificationSessionSerializer(serializers.ModelSerializer):
    """Serializer for ClassificationSession model"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    duration_minutes = serializers.SerializerMethodField()
    
    class Meta:
        model = ClassificationSession
        fields = [
            'id', 'user', 'user_email', 'started_at', 'ended_at',
            'classifications_count', 'total_time_seconds', 'duration_minutes'
        ]
        read_only_fields = ['id', 'user', 'started_at']
    
    def get_duration_minutes(self, obj):
        if obj.ended_at and obj.started_at:
            delta = obj.ended_at - obj.started_at
            return round(delta.total_seconds() / 60, 2)
        return None


class UserStatsSerializer(serializers.Serializer):
    """Serializer for user statistics"""
    total_classifications = serializers.IntegerField()
    training_classifications = serializers.IntegerField()
    regular_classifications = serializers.IntegerField()
    reliability_score = serializers.FloatField()
    agreement_with_gold = serializers.FloatField()
    level = serializers.IntegerField()
    points = serializers.IntegerField()
    badges = serializers.ListField()
    rank = serializers.IntegerField(required=False)
    total_users = serializers.IntegerField(required=False)


class GeneralStatsSerializer(serializers.Serializer):
    """Serializer for general statistics (GDPR-compliant, anonymous)"""
    project = serializers.DictField()
    activity = serializers.DictField()
    distribution = serializers.DictField()
    progress = serializers.DictField()


class MyStatsSerializer(serializers.Serializer):
    """Serializer for personal user statistics (GDPR-compliant)"""
    overview = serializers.DictField()
    my_classifications = serializers.DictField()
    activity_timeline = serializers.DictField()
    comparison = serializers.DictField()
    recent_activity = serializers.ListField()


class SavedAbstractSerializer(serializers.ModelSerializer):
    """Serializer for SavedAbstract model with full abstract details"""
    abstract = AbstractListSerializer(read_only=True)
    abstract_id = serializers.IntegerField(write_only=True)
    abstract_classifications = serializers.SerializerMethodField()
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = SavedAbstract
        fields = [
            'id', 'user', 'user_email', 'abstract', 'abstract_id', 'abstract_classifications',
            'notes', 'tags', 'saved_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'saved_at', 'updated_at']
    
    def validate_abstract_id(self, value):
        """Validate that abstract exists"""
        from apps.abstracts.models import Abstract
        if not Abstract.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Abstract not found or inactive")
        return value
    
    def get_abstract_classifications(self, obj):
        """Get classification summary for this abstract"""
        from collections import Counter
        from .models import Category
        
        classifications = Classification.objects.filter(
            abstract=obj.abstract,
            is_valid=True
        )
        
        if not classifications.exists():
            return {
                'total': 0,
                'by_category': {},
                'meta_aspects': {}
            }
        
        # Get category names mapping
        categories = Category.objects.all()
        category_names = {cat.code: cat.name for cat in categories}
        
        main_counter = Counter()
        meta_counter = Counter()
        
        for c in classifications:
            main_counter[c.main_classification] += 1
            if c.meta_aspects:
                for aspect in c.meta_aspects:
                    meta_counter[aspect] += 1
        
        total = classifications.count()
        by_category = {
            category: {
                'count': count,
                'percentage': round((count / total * 100), 1),
                'display_name': category_names.get(category, category)
            }
            for category, count in main_counter.items()
        }
        
        meta_aspects = {
            aspect: {
                'count': count,
                'percentage': round((count / total * 100), 1),
                'display_name': category_names.get(aspect, aspect)
            }
            for aspect, count in meta_counter.items()
        }
        
        return {
            'total': total,
            'by_category': by_category,
            'meta_aspects': meta_aspects
        }
    
    def create(self, validated_data):
        """Create a saved abstract"""
        from apps.abstracts.models import Abstract
        
        abstract_id = validated_data.pop('abstract_id')
        abstract = Abstract.objects.get(id=abstract_id)
        validated_data['abstract'] = abstract
        validated_data['user'] = self.context['request'].user
        return SavedAbstract.objects.create(**validated_data)


class SavedAbstractListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing saved abstracts"""
    abstract_title = serializers.CharField(source='abstract.title', read_only=True)
    abstract_text = serializers.CharField(source='abstract.abstract_text', read_only=True)
    abstract_doi = serializers.CharField(source='abstract.doi', read_only=True)
    abstract_year = serializers.IntegerField(source='abstract.publication_year', read_only=True)
    abstract_journal = serializers.CharField(source='abstract.journal', read_only=True)
    abstract_keywords = serializers.CharField(source='abstract.keywords', read_only=True)
    abstract_wos_categories = serializers.CharField(source='abstract.wos_categories', read_only=True)
    abstract_research_areas = serializers.CharField(source='abstract.research_areas', read_only=True)
    abstract_classifications = serializers.SerializerMethodField()
    
    class Meta:
        model = SavedAbstract
        fields = [
            'id', 'abstract_id', 'abstract_title', 'abstract_text', 'abstract_doi', 
            'abstract_year', 'abstract_journal', 'abstract_keywords',
            'abstract_wos_categories', 'abstract_research_areas', 'abstract_classifications',
            'notes', 'tags', 'saved_at'
        ]
    
    def get_abstract_classifications(self, obj):
        """Get classification summary for this abstract"""
        from collections import Counter
        from .models import Category
        
        classifications = Classification.objects.filter(
            abstract=obj.abstract,
            is_valid=True
        )
        
        if not classifications.exists():
            return {
                'total': 0,
                'by_category': {},
                'meta_aspects': {}
            }
        
        # Get category names mapping
        categories = Category.objects.all()
        category_names = {cat.code: cat.name for cat in categories}
        
        main_counter = Counter()
        meta_counter = Counter()
        
        for c in classifications:
            main_counter[c.main_classification] += 1
            if c.meta_aspects:
                for aspect in c.meta_aspects:
                    meta_counter[aspect] += 1
        
        total = classifications.count()
        by_category = {
            category: {
                'count': count,
                'percentage': round((count / total * 100), 1),
                'display_name': category_names.get(category, category)
            }
            for category, count in main_counter.items()
        }
        
        meta_aspects = {
            aspect: {
                'count': count,
                'percentage': round((count / total * 100), 1),
                'display_name': category_names.get(aspect, aspect)
            }
            for aspect, count in meta_counter.items()
        }
        
        return {
            'total': total,
            'by_category': by_category,
            'meta_aspects': meta_aspects
        }


class SavedAbstractUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating notes and tags only"""
    
    class Meta:
        model = SavedAbstract
        fields = ['notes', 'tags']


class FollowedDebateSerializer(serializers.ModelSerializer):
    """Serializer for FollowedDebate model with full debate details"""
    debate = serializers.SerializerMethodField()
    debate_id = serializers.IntegerField(write_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = FollowedDebate
        fields = [
            'id', 'user', 'user_email', 'debate', 'debate_id', 'followed_at'
        ]
        read_only_fields = ['id', 'user', 'followed_at']
    
    def get_debate(self, obj):
        """Get debate details"""
        from .serializers import AbstractDebateSerializer
        return AbstractDebateSerializer(obj.debate, context=self.context).data
    
    def validate_debate_id(self, value):
        """Validate that debate exists"""
        from .models import AbstractDebate
        if not AbstractDebate.objects.filter(id=value).exists():
            raise serializers.ValidationError("Debate not found")
        return value
    
    def create(self, validated_data):
        """Create a followed debate"""
        from .models import AbstractDebate
        
        debate_id = validated_data.pop('debate_id')
        debate = AbstractDebate.objects.get(id=debate_id)
        validated_data['debate'] = debate
        validated_data['user'] = self.context['request'].user
        return FollowedDebate.objects.create(**validated_data)


class FollowedDebateListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing followed debates"""
    debate_text = serializers.CharField(source='debate.text', read_only=True)
    debate_abstract_id = serializers.IntegerField(source='debate.abstract.id', read_only=True)
    debate_abstract_title = serializers.CharField(source='debate.abstract.title', read_only=True)
    debate_initiator = serializers.SerializerMethodField()
    debate_comments_count = serializers.IntegerField(source='debate.comments_count', read_only=True)
    debate_is_closed = serializers.BooleanField(source='debate.is_closed', read_only=True)
    debate_created_at = serializers.DateTimeField(source='debate.created_at', read_only=True)
    
    class Meta:
        model = FollowedDebate
        fields = [
            'id', 'debate_id', 'debate_text', 'debate_abstract_id', 'debate_abstract_title',
            'debate_initiator', 'debate_comments_count',
            'debate_is_closed', 'debate_created_at', 'followed_at'
        ]
    
    def get_debate_initiator(self, obj):
        """Return initiator info only if profile is public"""
        initiator = obj.debate.initiator
        
        # Check if user has a public profile
        try:
            profile = initiator.classification_profile
            if profile.is_profile_public:
                return {
                    'username': initiator.username,
                    'email': initiator.email,
                    'is_public': True
                }
        except UserProfile.DoesNotExist:
            pass
        
        # Return anonymous info if profile is not public
        return {
            'username': None,
            'email': None,
            'is_public': False
        }


class ShareAbstractSerializer(serializers.Serializer):
    """
    Serializer for sharing abstracts via email
    POST data: {
        "abstract_id": 123,
        "recipient_email": "user@example.com",
        "message": "Check out this interesting abstract!"
    }
    """
    abstract_id = serializers.IntegerField(
        help_text="ID of the abstract to share"
    )
    recipient_email = serializers.EmailField(
        help_text="Email address of the recipient"
    )
    message = serializers.CharField(
        max_length=1000,
        required=False,
        allow_blank=True,
        help_text="Optional personal message to include in the email"
    )
    
    def validate_abstract_id(self, value):
        """Validate that abstract exists and is active"""
        from apps.abstracts.models import Abstract
        if not Abstract.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Abstract not found or inactive")
        return value
    
    def validate_recipient_email(self, value):
        """Validate email format"""
        return value.lower()


class ShareDebateSerializer(serializers.Serializer):
    """
    Serializer for sharing debates via email
    POST data: {
        "debate_id": 123,
        "recipient_email": "user@example.com",
        "message": "Check out this interesting debate!"
    }
    """
    debate_id = serializers.IntegerField(
        help_text="ID of the debate to share"
    )
    recipient_email = serializers.EmailField(
        help_text="Email address of the recipient"
    )
    message = serializers.CharField(
        max_length=1000,
        required=False,
        allow_blank=True,
        help_text="Optional personal message to include in the email"
    )
    
    def validate_debate_id(self, value):
        """Validate that debate exists"""
        from apps.classifications.models import AbstractDebate
        if not AbstractDebate.objects.filter(id=value).exists():
            raise serializers.ValidationError("Debate not found")
        return value
    
    def validate_recipient_email(self, value):
        """Validate email format"""
        return value.lower()


# ============================================
# Debate and Comment Serializers
# ============================================

class DebateCommentSerializer(serializers.ModelSerializer):
    """
    Serializer for debate comments (with user info)
    """
    user_display_name = serializers.SerializerMethodField()
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    text = serializers.SerializerMethodField()
    
    class Meta:
        model = DebateComment
        fields = [
            'id', 'user_id', 'user_display_name', 'text',
            'created_at', 'is_deleted', 'likes_count'
        ]
        read_only_fields = ['created_at', 'is_deleted', 'likes_count']
    
    def get_user_display_name(self, obj):
        """Return display name if public, otherwise Anonymous"""
        try:
            profile = obj.user.classification_profile
            if profile.is_profile_public:
                return profile.get_display_name()
        except UserProfile.DoesNotExist:
            pass
        return "Anonymous"
    
    def get_text(self, obj):
        """Show 'Comment deleted' for deleted comments"""
        if obj.is_deleted:
            return "[Comment deleted]"
        return obj.text


class DebateCommentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating comments (no editing allowed, like X)
    """
    class Meta:
        model = DebateComment
        fields = ['text']
    
    def validate_text(self, value):
        """Validate comment text"""
        if len(value.strip()) < 1:
            raise serializers.ValidationError("Comment cannot be empty")
        if len(value) > 350:
            raise serializers.ValidationError("Comment too long (max 350 characters)")
        return value.strip()
    
    def create(self, validated_data):
        """Create comment with user and debate from context"""
        from .models import Notification, FollowedDebate
        
        validated_data['user'] = self.context['request'].user
        validated_data['debate'] = self.context['debate']
        comment = super().create(validated_data)
        
        debate = self.context['debate']
        commenter = self.context['request'].user
        
        # Create notifications for relevant users
        notifications_to_create = []
        users_to_notify = set()  # Use set to avoid duplicate notifications
        
        # 1. Notify debate initiator (if not the commenter)
        if debate.initiator != commenter:
            users_to_notify.add(debate.initiator.id)
            notifications_to_create.append(
                Notification(
                    user=debate.initiator,
                    notification_type='debate_comment',
                    debate=debate,
                    comment=comment,
                    actor=commenter,
                    message=f"{commenter.username} commented on your debate"
                )
            )
        
        # 2. Notify all users following this debate (excluding commenter and initiator)
        followers = FollowedDebate.objects.filter(
            debate=debate
        ).exclude(user=commenter).select_related('user')
        
        for followed in followers:
            # Skip if already notified (e.g., if initiator also follows their own debate)
            if followed.user.id not in users_to_notify:
                users_to_notify.add(followed.user.id)
                notifications_to_create.append(
                    Notification(
                        user=followed.user,
                        notification_type='debate_comment',
                        debate=debate,
                        comment=comment,
                        actor=commenter,
                        message=f"{commenter.username} commented on a debate you're following"
                    )
                )
        
        # Bulk create notifications for efficiency
        if notifications_to_create:
            Notification.objects.bulk_create(notifications_to_create)
        
        return comment


class AbstractDebateSerializer(serializers.ModelSerializer):
    """
    Serializer for debate details (includes comments)
    """
    initiator_display_name = serializers.SerializerMethodField()
    initiator_id = serializers.IntegerField(source='initiator.id', read_only=True)
    abstract_id = serializers.IntegerField(source='abstract.id', read_only=True)
    abstract_title = serializers.CharField(source='abstract.title', read_only=True)
    abstract_text = serializers.CharField(source='abstract.abstract_text', read_only=True)
    abstract_classifications = serializers.SerializerMethodField()
    comments_count = serializers.ReadOnlyField()
    comments = serializers.SerializerMethodField()
    is_followed = serializers.SerializerMethodField()
    
    class Meta:
        model = AbstractDebate
        fields = [
            'id', 'abstract_id', 'abstract_title', 'abstract_text', 'abstract_classifications',
            'initiator_id', 'initiator_display_name',
            'text', 'created_at', 'updated_at', 'is_closed', 'is_pinned',
            'views_count', 'comments_count', 'comments', 'is_followed'
        ]
        read_only_fields = ['created_at', 'updated_at', 'views_count']
    
    def get_initiator_display_name(self, obj):
        """Return display name if public, otherwise Anonymous"""
        try:
            profile = obj.initiator.classification_profile
            if profile.is_profile_public:
                return profile.get_display_name()
        except UserProfile.DoesNotExist:
            pass
        return "Anonymous"
    
    def get_is_followed(self, obj):
        """Check if current user is following this debate"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            from .models import FollowedDebate
            return FollowedDebate.objects.filter(
                user=request.user,
                debate=obj
            ).exists()
        return False
    
    def get_abstract_classifications(self, obj):
        """Get classification summary for this abstract"""
        from collections import Counter
        from .models import Classification, Category
        
        # Get all classifications for this abstract
        classifications = Classification.objects.filter(
            abstract=obj.abstract,
            is_valid=True
        )
        
        if not classifications.exists():
            return {
                'total': 0,
                'by_category': {},
                'meta_aspects': {}
            }
        
        # Get category names mapping
        categories = Category.objects.all()
        category_names = {cat.code: cat.name for cat in categories}
        
        # Count by main category
        main_counter = Counter()
        meta_counter = Counter()
        
        for c in classifications:
            main_counter[c.main_classification] += 1
            
            # Count meta aspects if present
            if c.meta_aspects:
                for aspect in c.meta_aspects:
                    meta_counter[aspect] += 1
        
        # Convert to percentages with display names
        total = classifications.count()
        by_category = {
            category: {
                'count': count,
                'percentage': round((count / total * 100), 1),
                'display_name': category_names.get(category, category)
            }
            for category, count in main_counter.items()
        }
        
        meta_aspects = {
            aspect: {
                'count': count,
                'percentage': round((count / total * 100), 1),
                'display_name': category_names.get(aspect, aspect)
            }
            for aspect, count in meta_counter.items()
        }
        
        return {
            'total': total,
            'by_category': by_category,
            'meta_aspects': meta_aspects
        }
    
    def get_comments(self, obj):
        """Get all comments (flat list, no threading)"""
        comments = obj.comments.filter(is_deleted=False).order_by('created_at')
        return DebateCommentSerializer(comments, many=True).data


class AbstractDebateListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing debates (no comments)
    """
    initiator_display_name = serializers.SerializerMethodField()
    initiator_id = serializers.IntegerField(source='initiator.id', read_only=True)
    abstract_id = serializers.IntegerField(source='abstract.id', read_only=True)
    abstract_title = serializers.CharField(source='abstract.title', read_only=True)
    abstract_text = serializers.CharField(source='abstract.abstract_text', read_only=True)
    abstract_classifications = serializers.SerializerMethodField()
    comments_count = serializers.ReadOnlyField()
    is_followed = serializers.SerializerMethodField()
    
    class Meta:
        model = AbstractDebate
        fields = [
            'id', 'abstract_id', 'abstract_title', 'abstract_text', 'abstract_classifications',
            'initiator_id', 'initiator_display_name',
            'text', 'created_at', 'is_closed', 'is_pinned',
            'views_count', 'comments_count', 'is_followed'
        ]
    
    def get_initiator_display_name(self, obj):
        """Return display name if public, otherwise Anonymous"""
        try:
            profile = obj.initiator.classification_profile
            if profile.is_profile_public:
                return profile.get_display_name()
        except UserProfile.DoesNotExist:
            pass
        return "Anonymous"
    
    def get_is_followed(self, obj):
        """Check if current user is following this debate"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            from .models import FollowedDebate
            return FollowedDebate.objects.filter(
                user=request.user,
                debate=obj
            ).exists()
        return False
    
    def get_abstract_classifications(self, obj):
        """Get classification summary for this abstract"""
        from collections import Counter
        from .models import Classification, Category
        
        classifications = Classification.objects.filter(
            abstract=obj.abstract,
            is_valid=True
        )
        
        if not classifications.exists():
            return {
                'total': 0,
                'by_category': {},
                'meta_aspects': {}
            }
        
        # Get category names mapping
        categories = Category.objects.all()
        category_names = {cat.code: cat.name for cat in categories}
        
        main_counter = Counter()
        meta_counter = Counter()
        
        for c in classifications:
            main_counter[c.main_classification] += 1
            if c.meta_aspects:
                for aspect in c.meta_aspects:
                    meta_counter[aspect] += 1
        
        total = classifications.count()
        by_category = {
            category: {
                'count': count,
                'percentage': round((count / total * 100), 1),
                'display_name': category_names.get(category, category)
            }
            for category, count in main_counter.items()
        }
        
        meta_aspects = {
            aspect: {
                'count': count,
                'percentage': round((count / total * 100), 1),
                'display_name': category_names.get(aspect, aspect)
            }
            for aspect, count in meta_counter.items()
        }
        
        return {
            'total': total,
            'by_category': by_category,
            'meta_aspects': meta_aspects
        }


class AbstractDebateCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating debates - frontend sends: {abstract: id, text: text}
    """
    class Meta:
        model = AbstractDebate
        fields = ['abstract', 'text']
    
    def validate_text(self, value):
        """Validate debate text"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Text too short (min 10 characters)")
        return value.strip()
    
    def validate_abstract(self, value):
        """Validate abstract exists and is active"""
        if not value.is_active:
            raise serializers.ValidationError("Abstract is not active")
        return value
    
    def create(self, validated_data):
        """Create debate with initiator from request"""
        validated_data['initiator'] = self.context['request'].user
        return super().create(validated_data)


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification model
    """
    actor_username = serializers.CharField(source='actor.username', read_only=True)
    debate_id = serializers.IntegerField(source='debate.id', read_only=True)
    abstract_title = serializers.CharField(source='debate.abstract.title', read_only=True)
    abstract_id = serializers.IntegerField(source='debate.abstract.id', read_only=True)
    comment_text = serializers.SerializerMethodField()
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'notification_type_display',
            'actor_username', 'message', 'is_read', 'read_at',
            'debate_id', 'abstract_title', 'abstract_id',
            'comment_text', 'created_at'
        ]
        read_only_fields = [
            'id', 'notification_type', 'actor_username', 'message',
            'debate_id', 'abstract_title', 'abstract_id', 'created_at'
        ]
    
    def get_comment_text(self, obj):
        """Get preview of comment text"""
        if obj.comment and not obj.comment.is_deleted:
            text = obj.comment.text
            return text[:100] + '...' if len(text) > 100 else text
        return None


class NotificationListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for notification list
    """
    actor_username = serializers.CharField(source='actor.username', read_only=True)
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    debate_id = serializers.IntegerField(source='debate.id', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'notification_type_display',
            'actor_username', 'message', 'is_read', 'debate_id',
            'created_at'
        ]
