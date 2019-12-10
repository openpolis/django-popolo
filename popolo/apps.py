from django.apps import AppConfig


class PopoloConfig(AppConfig):
    """
    Default "popolo" app configuration.
    """

    name = "popolo"
    verbose_name = "Popolo"

    def ready(self):
        from popolo import admin
        from popolo import signals

        admin.register()  # Register models in admin site
        signals.connect()  # Connect the signals


class PopoloNoAdminConfig(PopoloConfig):
    """
    Alternate "popolo" app configuration which doesn't load the admin site.

    Useful in tests.
    """

    def ready(self):
        from popolo import signals

        signals.connect()  # Just connect the signals
