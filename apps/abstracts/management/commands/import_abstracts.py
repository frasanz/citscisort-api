import csv
from django.core.management.base import BaseCommand
from apps.abstracts.models import Abstract


class Command(BaseCommand):
    help = 'Import abstracts from abstracts.txt TSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='abstracts.txt',
            help='Path to the TSV file (default: abstracts.txt)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing abstracts before importing'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing abstracts...'))
            Abstract.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Abstracts cleared.'))

        self.stdout.write(f'Reading abstracts from {file_path}...')
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                # Usar DictReader con tabulador como delimitador
                reader = csv.DictReader(file, delimiter='\t')
                
                for row_num, row in enumerate(reader, start=2):  # start=2 porque línea 1 es header
                    try:
                        # Extraer campos relevantes del TSV
                        publication_type = row.get('PT', 'J').strip()[:1] or 'J'  # Default to Journal
                        title = row.get('TI', '').strip()
                        abstract_text = row.get('AB', '').strip()
                        authors = row.get('AU', '').strip()
                        publication_year = row.get('PY', '').strip()
                        journal = row.get('SO', '').strip()
                        doi = row.get('DI', '').strip()
                        keywords = row.get('DE', '').strip()
                        
                        # Nuevos campos bibliométricos (Web of Science)
                        affiliations = row.get('C1', '').strip()  # Author addresses
                        times_cited_str = row.get('TC', '0').strip()  # Times cited
                        wos_categories = row.get('WC', '').strip()  # WoS categories
                        research_areas = row.get('SC', '').strip()  # Research areas
                        
                        # Validar que tenga al menos título y abstract
                        if not title or not abstract_text:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Línea {row_num}: Saltando registro sin título o abstract'
                                )
                            )
                            skipped_count += 1
                            continue
                        
                        # Convertir año a entero
                        year = None
                        if publication_year:
                            try:
                                year = int(publication_year)
                            except ValueError:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'Línea {row_num}: Año inválido "{publication_year}"'
                                    )
                                )
                        
                        # Convertir times_cited a entero
                        times_cited = 0
                        if times_cited_str:
                            try:
                                times_cited = int(times_cited_str)
                            except ValueError:
                                pass  # Mantener default 0
                        
                        # Preparar datos base
                        base_data = {
                            'title': title[:500],
                            'abstract_text': abstract_text,
                            'authors': authors[:1000] if authors else '',
                            'publication_year': year,
                            'publication_type': publication_type,
                            'journal': journal[:200] if journal else '',
                            'keywords': keywords[:500] if keywords else '',
                            'affiliations': affiliations,
                            'times_cited': times_cited,
                            'wos_categories': wos_categories,
                            'research_areas': research_areas,
                        }
                        
                        # Datos solo para creación (no actualizar si ya existe)
                        defaults = {
                            **base_data,
                            'required_classifications': 5,
                            'current_classifications_count': 0,
                            'is_gold_standard': False,
                            'consensus_reached': False,
                            'gold_classifications_complete': False,
                            'times_shown': 0
                        }
                        
                        # Usar DOI como clave única si existe, sino crear siempre
                        if doi:
                            abstract, created = Abstract.objects.update_or_create(
                                doi=doi[:200],
                                defaults=defaults
                            )
                            if created:
                                created_count += 1
                            else:
                                # Actualizar solo campos bibliométricos en abstracts existentes
                                Abstract.objects.filter(doi=doi[:200]).update(
                                    affiliations=affiliations,
                                    times_cited=times_cited,
                                    wos_categories=wos_categories,
                                    research_areas=research_areas,
                                )
                                updated_count += 1
                        else:
                            # Sin DOI, crear directamente (no podemos identificar duplicados)
                            Abstract.objects.create(**defaults)
                            created_count += 1
                        
                        # Mostrar progreso cada 50 registros
                        total_processed = created_count + updated_count
                        if total_processed % 50 == 0:
                            self.stdout.write(f'  Procesados: {total_processed} (creados: {created_count}, actualizados: {updated_count})...')
                    
                    except Exception as e:
                        error_count += 1
                        self.stdout.write(
                            self.style.ERROR(
                                f'Línea {row_num}: Error al importar - {str(e)}'
                            )
                        )
        
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'Archivo no encontrado: {file_path}')
            )
            return
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al leer el archivo: {str(e)}')
            )
            return

        # Resumen final
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'✓ Creados: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'✓ Actualizados: {updated_count}'))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'⚠ Saltados (sin título/abstract): {skipped_count}'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'✗ Errores: {error_count}'))
        self.stdout.write('='*60)
