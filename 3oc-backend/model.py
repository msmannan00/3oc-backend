from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # Add additional fields if needed
    # For example:
    # bio = models.TextField(blank=True, null=True)
    pass

    def __str__(self):
        return self.username
