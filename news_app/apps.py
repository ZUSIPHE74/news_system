from django.apps import AppConfig


class NewsAppConfig(AppConfig):
    """Application configuration for the news app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "news_app"

    def ready(self):
        """Register signal handlers when the app is loaded."""
        import news_app.signals  # noqa: F401
