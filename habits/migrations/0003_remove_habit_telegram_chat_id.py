# Generated by Django 4.2.18 on 2025-02-04 20:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('habits', '0002_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='habit',
            name='telegram_chat_id',
        ),
    ]
