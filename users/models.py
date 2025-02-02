from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    telegram_chat_id = models.CharField(max_length=50, blank=True, null=True)
