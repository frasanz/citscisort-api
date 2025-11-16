from django.apps import AppConfig


class ClassificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.classifications'
    
    def ready(self):
        import apps.classifications.signals  # noqa
