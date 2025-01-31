from django.db import models
from django.contrib.auth.models import User
from .validators import (
    validate_related_habit,
    validate_habit_time,
    validate_habit_frequency,
    validate_habit_reward,
    validate_pleasant_habit
)


class Habit(models.Model):
    objects = None
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='habits')
    place = models.CharField(max_length=100)
    time = models.TimeField()
    action = models.CharField(max_length=255)
    is_pleasant = models.BooleanField(default=False)
    related_habit = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True)
    frequency = models.PositiveIntegerField(default=1)
    reward = models.CharField(max_length=255, blank=True)
    duration = models.PositiveIntegerField()  # в секундах
    is_public = models.BooleanField(default=False)
    telegram_chat_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.action} в {self.time} в {self.place}"

    def clean(self):
        validate_related_habit(self)
        validate_habit_time(self)
        validate_habit_frequency(self)
        validate_habit_reward(self)
        validate_pleasant_habit(self)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['time']
