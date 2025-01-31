from celery import shared_task
from .models import Habit
from .telegram_bot import send_reminder
from django.utils import timezone


@shared_task
def send_habit_reminders():
    current_time = timezone.now().time()
    habits = Habit.objects.filter(
        time__hour=current_time.hour, time__minute=current_time.minute)
    for habit in habits:
        if habit.telegram_chat_id:
            send_reminder(habit.telegram_chat_id, habit.action)
