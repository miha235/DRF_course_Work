# habits/validators.py
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from datetime import datetime


def validate_related_habit(habit):
    if habit.related_habit and not habit.related_habit.is_pleasant:
        raise ValidationError(_('Связанная привычка должна быть приятной.'))


def validate_habit_time(habit):
    if isinstance(habit.time, str):  # Преобразуем строку в time, если это строка
        habit.time = datetime.strptime(habit.time, "%H:%M:%S").time()

    total_seconds = habit.time.minute * 60 + habit.time.second
    if total_seconds < 300:
        raise ValidationError("Минимальное время должно быть 5 минут")




def validate_habit_frequency(habit):
    if habit.frequency > 7:
        raise ValidationError(
            _('Нельзя выполнять привычку реже, чем раз в 7 дней.'))


def validate_habit_reward(habit):
    if habit.reward and habit.related_habit:
        raise ValidationError(
            _('Нельзя одновременно указывать вознаграждение и связанную привычку.'))


def validate_pleasant_habit(habit):
    if habit.is_pleasant and (habit.reward or habit.related_habit):
        raise ValidationError(
            _('У приятной привычки не может быть вознаграждения или связанной привычки.'))
