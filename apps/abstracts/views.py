from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Q, Count, Exists, OuterRef, F, Avg
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from drf_spectacular.utils import extend_schema, OpenApiResponse
import random
from .models import Abstract
from .serializers import (
    AbstractSerializer, AbstractListSerializer,
    AbstractClassificationSerializer
)
from apps.classifications.models import Classification, SharedAbstract
from apps.classifications.serializers import ShareAbstractSerializer


class AbstractViewSet(viewsets.ModelViewSet):
    """
    ViewSet for abstracts
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AbstractListSerializer
        return AbstractSerializer
    
    def get_queryset(self):
        queryset = Abstract.objects.filter(is_active=True)
        
        # Filters
        is_gold = self.request.query_params.get('is_gold')
        needs_classification = self.request.query_params.get('needs_classification')
        
        if is_gold:
            queryset = queryset.filter(is_gold_standard=True)
        
        if needs_classification:
            queryset = queryset.filter(
                current_classifications_count__lt=F('required_classifications'),
                consensus_reached=False
            )
        
        return queryset.select_related().order_by('-created_at')
    
    def get_permissions(self):
        """Admin-only for create, update, delete"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get overall statistics about abstracts"""
        total = Abstract.objects.filter(is_active=True).count()
        gold_standards = Abstract.objects.filter(is_gold_standard=True, is_active=True).count()
        consensus_reached = Abstract.objects.filter(consensus_reached=True, is_active=True).count()
        
        needs_classification = Abstract.objects.filter(
            is_active=True,
            consensus_reached=False
        ).count()
        
        avg_classifications = Abstract.objects.filter(
            is_active=True
        ).aggregate(
            avg=Avg('current_classifications_count')
        )['avg'] or 0
        
        return Response({
            'total_abstracts': total,
            'gold_standards': gold_standards,
            'consensus_reached': consensus_reached,
            'needs_classification': needs_classification,
            'average_classifications_per_abstract': round(avg_classifications, 2),
        })
    
    @extend_schema(
        request=ShareAbstractSerializer,
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'message': {'type': 'string'},
                    'shared_id': {'type': 'integer'},
                    'shared_at': {'type': 'string', 'format': 'date-time'}
                }
            },
            500: {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'error': {'type': 'string'}
                }
            }
        },
        description="Share an abstract via email. Requires abstract_id, recipient_email, and optional message."
    )
    @action(detail=False, methods=['post'])
    def share(self, request):
        """
        Share an abstract via email
        POST /api/abstracts/share/
        
        Body: {
            "abstract_id": 123,
            "recipient_email": "user@example.com",
            "message": "Check out this abstract!"
        }
        """
        serializer = ShareAbstractSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Get validated data
        abstract_id = serializer.validated_data['abstract_id']
        recipient_email = serializer.validated_data['recipient_email']
        user_message = serializer.validated_data.get('message', '')
        
        # Get the abstract
        abstract = Abstract.objects.get(id=abstract_id, is_active=True)
        
        # Prepare email context - use display name if available
        try:
            profile = request.user.classification_profile
            sender_name = profile.get_display_name()
        except:
            sender_name = request.user.email
        
        abstract_url = f"{settings.FRONTEND_URL}/abstracts/{abstract.id}"
        
        context = {
            'sender_name': sender_name,
            'abstract': abstract,
            'abstract_url': abstract_url,
            'user_message': user_message,
        }
        
        # Render email templates
        subject = render_to_string('emails/abstracts/share_abstract_subject.txt', context).strip()
        text_message = render_to_string('emails/abstracts/share_abstract_message.txt', context)
        html_message = render_to_string('emails/abstracts/share_abstract_message.html', context)
        
        # Send email
        try:
            send_mail(
                subject=subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                html_message=html_message,
                fail_silently=False,
            )
            
            # Save to database
            shared_abstract = SharedAbstract.objects.create(
                user=request.user,
                abstract=abstract,
                recipient_email=recipient_email,
                message=user_message,
                email_sent_successfully=True
            )
            
            return Response({
                'success': True,
                'message': f'Abstract shared successfully with {recipient_email}',
                'shared_id': shared_abstract.id,
                'shared_at': shared_abstract.shared_at
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Log error and save failed attempt
            SharedAbstract.objects.create(
                user=request.user,
                abstract=abstract,
                recipient_email=recipient_email,
                message=user_message,
                email_sent_successfully=False
            )
            
            return Response({
                'success': False,
                'error': 'Failed to send email. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def my_shared(self, request):
        """
        Get list of abstracts I have shared
        GET /api/abstracts/my_shared/
        """
        shared_abstracts = SharedAbstract.objects.filter(
            user=request.user
        ).select_related('abstract').order_by('-shared_at')[:50]
        
        results = []
        for shared in shared_abstracts:
            results.append({
                'id': shared.id,
                'abstract_id': shared.abstract.id,
                'abstract_title': shared.abstract.title,
                'recipient_email': shared.recipient_email,
                'message': shared.message,
                'shared_at': shared.shared_at,
                'email_sent_successfully': shared.email_sent_successfully
            })
        
        return Response({
            'shared_abstracts': results,
            'total': len(results)
        })
    
    @action(detail=False, methods=['get'])
    def most_shared(self, request):
        """
        Get most shared abstracts (community statistics)
        GET /api/abstracts/most_shared/?limit=10
        """
        limit = int(request.query_params.get('limit', 10))
        
        most_shared = Abstract.objects.filter(
            is_active=True
        ).annotate(
            shares_count=Count('shared_by_users')
        ).filter(
            shares_count__gt=0
        ).order_by('-shares_count')[:limit]
        
        results = []
        for abstract in most_shared:
            data = AbstractListSerializer(abstract).data
            data['shares_count'] = abstract.shares_count
            results.append(data)
        
        return Response({
            'most_shared': results,
            'note': 'Anonymous community statistics - shows how many times each abstract was shared'
        })
