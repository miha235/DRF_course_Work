import os
from telegram.ext import Updater, CommandHandler
from django.conf import settings

TOKEN = settings.TELEGRAM_BOT_TOKEN
BOT_USERNAME = 'OurHaBitBot'


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"Привет! Я бот @{BOT_USERNAME} для отслеживания привычек.")


def setup_bot():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    return updater


def send_reminder(chat_id, habit_name):
    bot = setup_bot().bot
    bot.send_message(
        chat_id=chat_id, text=f"Напоминание: Пора выполнить привычку '{habit_name}'!")


if __name__ == '__main__':
    updater = setup_bot()
    updater.start_polling()
    updater.idle()
