from django.contrib import admin
from .models import Abstract


@admin.register(Abstract)
class AbstractAdmin(admin.ModelAdmin):
    list_display = ['doi', 'short_title', 'publication_year', 'current_classifications_count', 
                    'required_classifications', 'is_gold_standard', 'consensus_reached', 'is_active']
    list_filter = ['is_gold_standard', 'consensus_reached', 'is_active', 'publication_year']
    search_fields = ['doi', 'title', 'authors', 'keywords']
    readonly_fields = ['current_classifications_count', 'difficulty_score', 'created_at', 'updated_at']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Article Information', {
            'fields': ('title', 'authors', 'abstract_text', 'keywords', 'doi', 'publication_year', 'journal', 'url')
        }),
        ('Classification Configuration', {
            'fields': ('required_classifications', 'current_classifications_count', 'difficulty_score', 
                      'consensus_reached', 'is_gold_standard', 'gold_classifications_complete')
        }),
        ('Control', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )
    
    def short_title(self, obj):
        return obj.title[:60] + '...' if len(obj.title) > 60 else obj.title
    short_title.short_description = 'Title'
