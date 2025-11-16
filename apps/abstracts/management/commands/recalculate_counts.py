from django.core.management.base import BaseCommand
from apps.abstracts.models import Abstract
from apps.classifications.models import Classification


class Command(BaseCommand):
    help = 'Recalculate current_classifications_count for all abstracts'

    def handle(self, *args, **options):
        self.stdout.write('Recalculating classification counts...')
        
        updated = 0
        for abstract in Abstract.objects.filter(is_active=True):
            # Count valid classifications
            count = Classification.objects.filter(
                abstract=abstract,
                is_valid=True
            ).count()
            
            # Update if different
            if abstract.current_classifications_count != count:
                abstract.current_classifications_count = count
                
                # Update consensus_reached
                if count >= abstract.required_classifications:
                    abstract.consensus_reached = True
                else:
                    abstract.consensus_reached = False
                
                abstract.save(update_fields=['current_classifications_count', 'consensus_reached'])
                updated += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Updated {updated} abstracts')
        )
