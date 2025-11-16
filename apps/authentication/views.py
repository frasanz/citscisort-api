from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.contrib.auth import get_user_model

from .serializers import DeleteAccountSerializer
from apps.classifications.models import Classification, UserProfile

User = get_user_model()


class DeleteAccountView(APIView):
    """
    DELETE /api/auth/delete-account/
    
    Delete user account with two options:
    1. delete_classifications=true: Delete user and all their classifications (cascade)
    2. delete_classifications=false: Delete user but keep classifications anonymously (user set to null)
    
    Request body:
        {
            "delete_classifications": false,  // optional, default: false
            "confirm": true  // required
        }
    
    Response:
        {
            "message": "Account deleted successfully. X classifications were preserved anonymously.",
            "deleted_user": "user@example.com",
            "classifications_deleted": false,
            "classification_count": X
        }
    """
    permission_classes = [IsAuthenticated]
    serializer_class = DeleteAccountSerializer
    
    def delete(self, request):
        """Handle account deletion"""
        serializer = DeleteAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        delete_classifications = serializer.validated_data.get('delete_classifications', False)
        
        # Get user's classification count before deletion
        classification_count = Classification.objects.filter(user=user).count()
        
        try:
            with transaction.atomic():
                if delete_classifications:
                    # Option 1: Delete user and all their classifications (cascade)
                    Classification.objects.filter(user=user).delete()
                    message = f"Account deleted successfully. {classification_count} classifications were also deleted."
                else:
                    # Option 2: Delete user but keep classifications (set user to null)
                    # Update classifications to set user to null (anonymize)
                    Classification.objects.filter(user=user).update(user=None)
                    message = f"Account deleted successfully. {classification_count} classifications were preserved anonymously."
                
                # Delete user profile (will cascade to user due to OneToOneField)
                try:
                    profile = UserProfile.objects.get(user=user)
                    profile.delete()
                except UserProfile.DoesNotExist:
                    pass
                
                # Store user email before deletion
                user_email = user.email
                
                # Finally delete the user
                user.delete()
            
            return Response({
                'message': message,
                'deleted_user': user_email,
                'classifications_deleted': delete_classifications,
                'classification_count': classification_count
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Error deleting account: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
