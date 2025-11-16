from django.core.management.base import BaseCommand
from apps.classifications.models import Category


class Command(BaseCommand):
    help = 'Populate simplified categories (3 main + 7 meta aspects)'

    def handle(self, *args, **options):
        self.stdout.write('Deleting existing categories...')
        
        # Delete existing categories first
        deleted_count = Category.objects.all().delete()[0]
        self.stdout.write(f'Deleted {deleted_count} existing categories\n')
        
        self.stdout.write('Creating categories...')
        
        # 1. MAIN CLASSIFICATION (required, single choice)
        main_cats = [
            {
                'code': 'main_scientific_results',
                'name': 'Scientific Results',
                'description': 'The paper presents scientific findings, discoveries, or data analysis from a citizen science project. Examples: new species discovered, supernova observations, climate data patterns, disease mapping results, biodiversity findings, astronomical discoveries.',
                'order': 1
            },
            {
                'code': 'main_meta_research',
                'name': 'Meta-research',
                'description': 'The paper analyzes the citizen science project itself (methodology, participant engagement, data quality, project design) OR studies citizen science as a field (comparative studies, frameworks, platforms, best practices). Examples: analyzing volunteer retention, comparing data quality methods, evaluating mobile apps, studying participant motivations.',
                'order': 2
            },
            {
                'code': 'main_not_sure',
                'name': 'Not Sure',
                'description': 'The abstract does not provide enough information to determine the type, or it is unclear whether it fits into the above categories.',
                'order': 3
            },
        ]
        
        created_main = {}
        for cat in main_cats:
            obj, created = Category.objects.get_or_create(
                code=cat['code'],
                defaults={
                    'name': cat['name'],
                    'description': cat['description'],
                    'category_type': 'main',
                    'order': cat['order'],
                    'allows_multiple': False,
                }
            )
            created_main[cat['code']] = obj
            self.stdout.write(f"  {'Created' if created else 'Exists'}: {obj.name}")
        
        # 2. META-RESEARCH ASPECTS (multiple choice, conditional)
        meta_research_cat = created_main['main_meta_research']
        
        meta_aspects = [
            {
                'code': 'meta_participation',
                'name': 'Participation & Engagement',
                'description': 'Focus on participant motivations, retention, demographics, recruitment strategies, volunteer behavior',
                'order': 1
            },
            {
                'code': 'meta_data_quality',
                'name': 'Data Quality & Validation',
                'description': 'Focus on data accuracy, validation methods, comparison with expert data, quality control mechanisms',
                'order': 2
            },
            {
                'code': 'meta_methodology',
                'name': 'Methodology & Design',
                'description': 'Focus on project design, protocols, data collection methods, implementation strategies, workflows',
                'order': 3
            },
            {
                'code': 'meta_impact',
                'name': 'Impact & Outcomes',
                'description': 'Focus on scientific, educational, social, or policy impact; learning outcomes; community benefits',
                'order': 4
            },
            {
                'code': 'meta_technology',
                'name': 'Technology & Platforms',
                'description': 'Focus on apps, tools, platforms, gamification, AI, machine learning, technological infrastructure',
                'order': 5
            },
            {
                'code': 'meta_ethics',
                'name': 'Ethics & Legal',
                'description': 'Focus on privacy, data ownership, authorship, credit attribution, equity, accessibility, ethical concerns',
                'order': 6
            },
            {
                'code': 'meta_theory',
                'name': 'Theory & Framework',
                'description': 'Focus on definitions, typologies, theoretical frameworks, conceptual models, citizen science as a field of study',
                'order': 7
            },
        ]
        
        for aspect in meta_aspects:
            obj, created = Category.objects.get_or_create(
                code=aspect['code'],
                defaults={
                    'name': aspect['name'],
                    'description': aspect['description'],
                    'category_type': 'meta_aspect',
                    'order': aspect['order'],
                    'allows_multiple': True,
                    'show_if_parent_category': meta_research_cat,
                    'show_if_parent_values': ['main_meta_research'],
                }
            )
            self.stdout.write(f"  {'Created' if created else 'Exists'}: {obj.name}")
        
        total = Category.objects.count()
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully created {total} categories!'))
        self.stdout.write(self.style.SUCCESS(f'  - {Category.objects.filter(category_type="main").count()} main classifications'))
        self.stdout.write(self.style.SUCCESS(f'  - {Category.objects.filter(category_type="meta_aspect").count()} meta-research aspects'))
