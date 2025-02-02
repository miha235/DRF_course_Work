import requests
from django.conf import settings


def send_reminder(chat_id, habit_name):
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    message = f"Напоминание: Пора выполнить привычку '{habit_name}'!"
    payload = {
        'chat_id': chat_id,
        'text': message
    }
    requests.post(url, data=payload)


