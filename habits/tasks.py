# habits/tasks.py
from celery import shared_task
from .models import Habit
from .telegram_bot import send_reminder


@shared_task
def send_habit_reminders():
    # Фильтруем привычки, у которых есть пользователь с telegram_chat_id
    habits = Habit.objects.select_related ( 'user' ).exclude ( user__telegram_chat_id__isnull = True )

    for habit in habits:
        telegram_chat_id = habit.user.telegram_chat_id  # Берем chat_id через пользователя
        if telegram_chat_id:
            response = send_reminder ( telegram_chat_id,habit.action )

            # Проверяем статус ответа
            if response.status_code != 200:
                # Обрабатываем ошибку, например, логируем
                print ( f"Ошибка отправки уведомления для {telegram_chat_id}: {response.text}" )
