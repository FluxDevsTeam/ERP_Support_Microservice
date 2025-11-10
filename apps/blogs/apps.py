from django.apps import AppConfig


class BlogsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.blogs'
    verbose_name = 'Blog Management'
    path = 'c:\\Users\\HomePC\\Desktop\\FluxDevs\\ERP_SAAS\\ERP_Support_Microservice\\apps\\blogs'
    
    def ready(self):
        import apps.blogs.signals  # Register signal handlers