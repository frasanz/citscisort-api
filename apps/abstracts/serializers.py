from rest_framework import serializers
from .models import Abstract


class AbstractSerializer(serializers.ModelSerializer):
    """Serializer for Abstract model"""
    needs_more_classifications = serializers.BooleanField(read_only=True)
    abstract_classifications = serializers.SerializerMethodField()
    
    class Meta:
        model = Abstract
        fields = [
            'id', 'title', 'authors', 'abstract_text', 'keywords',
            'doi', 'publication_year', 'journal', 'url',
            'affiliations', 'times_cited', 'wos_categories', 'research_areas',
            'required_classifications', 'current_classifications_count',
            'difficulty_score', 'consensus_reached',
            'is_gold_standard', 'gold_classifications_complete',
            'needs_more_classifications', 'abstract_classifications',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'current_classifications_count', 'difficulty_score',
            'consensus_reached', 'gold_classifications_complete',
            'created_at', 'updated_at'
        ]
    
    def get_abstract_classifications(self, obj):
        """Get aggregated classification statistics for this abstract"""
        from collections import Counter
        from apps.classifications.models import Classification, Category
        
        classifications = Classification.objects.filter(
            abstract=obj, is_valid=True
        )
        
        if not classifications.exists():
            return {'total': 0, 'by_category': {}, 'meta_aspects': {}}
        
        # Build category code -> name mapping
        categories = Category.objects.all()
        category_names = {cat.code: cat.name for cat in categories}
        
        # Aggregate classifications using Counter
        main_counter = Counter()
        meta_counter = Counter()
        
        for c in classifications:
            main_counter[c.main_classification] += 1
            if c.meta_aspects:
                for aspect in c.meta_aspects:
                    meta_counter[aspect] += 1
        
        total = classifications.count()
        
        # Build response with count, percentage, display_name
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


class AbstractListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing abstracts"""
    
    class Meta:
        model = Abstract
        fields = [
            'id', 'doi', 'title', 'publication_year', 'times_cited',
            'current_classifications_count', 'required_classifications',
            'consensus_reached'
        ]


class AbstractClassificationSerializer(serializers.ModelSerializer):
    """Serializer for abstract when being classified (no spoilers)"""
    
    class Meta:
        model = Abstract
        fields = [
            'id', 'title', 'authors', 'abstract_text', 'keywords',
            'doi', 'publication_year', 'journal', 'url'
        ]
