from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from .models import Habit
from .tasks import send_habit_reminders
from .validators import validate_related_habit, validate_habit_time, validate_habit_frequency
from unittest.mock import patch, Mock
from django.core.exceptions import ValidationError


class HabitAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        self.habit_data = {
            'place': 'Дом',
            'time': '08:00:00',
            'action': 'Утренняя зарядка',
            'duration': 600,
            'frequency': 1,
            'reward': 'Чашка кофе',
            'is_public': True
        }

    def test_create_habit(self):
        response = self.client.post('/api/habits/', self.habit_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Habit.objects.count(), 1)

    def test_update_habit(self):
        habit = Habit.objects.create(user=self.user, **self.habit_data)
        updated_data = {'action': 'Вечерняя пробежка'}
        response = self.client.patch(f'/api/habits/{habit.id}/', updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        habit.refresh_from_db()
        self.assertEqual(habit.action, 'Вечерняя пробежка')

    def test_delete_habit(self):
        habit = Habit.objects.create(user=self.user, **self.habit_data)
        response = self.client.delete(f'/api/habits/{habit.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Habit.objects.count(), 0)


class TasksTestCase(TestCase):
    @patch('habits.tasks.send_reminder')
    def test_send_habit_reminders(self, mock_send_reminder):
        user = User.objects.create_user(username='testuser', password='12345')
        Habit.objects.create(
            user=user, action='Test Habit', place='Home', time=timezone.now().time(), duration=60, telegram_chat_id='123456'
        )
        send_habit_reminders()
        mock_send_reminder.assert_called_once()


class ValidatorsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_validate_related_habit(self):
        pleasant_habit = Habit.objects.create(user=self.user, action='Приятная привычка', is_pleasant=True)
        habit = Habit(user=self.user, action='Обычная привычка', related_habit=pleasant_habit)
        validate_related_habit(habit)

    def test_validate_habit_time(self):
        habit = Habit(user=self.user, action='Тест времени', duration=120)
        validate_habit_time(habit)

        habit.duration = 121
        with self.assertRaises(ValidationError):
            validate_habit_time(habit)

    def test_validate_habit_frequency(self):
        habit = Habit(user=self.user, action='Тест частоты', frequency=7)
        validate_habit_frequency(habit)

        habit.frequency = 8
        with self.assertRaises(ValidationError):
            validate_habit_frequency(habit)
