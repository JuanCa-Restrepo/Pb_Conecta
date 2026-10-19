from rest_framework.exceptions import ValidationError


class ErrorRegla(ValidationError):
    """Incumplimiento de una regla de negocio. Responde 400 con {"detail": [mensaje]}."""

    def __init__(self, mensaje):
        super().__init__({"detail": mensaje})
