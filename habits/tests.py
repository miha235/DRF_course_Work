from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.utils import timezone
from .models import Habit
from .permissions import IsOwnerOrReadOnly
from .serializers import HabitSerializer, PublicHabitSerializer
from .tasks import send_habit_reminders
from .telegram_bot import send_reminder, setup_bot
from .validators import validate_related_habit, validate_habit_time, validate_habit_frequency
from unittest.mock import patch, Mock
from django.core.exceptions import ValidationError
from django.utils import timezone


class HabitAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        self.habit_data = {
            'place': 'Дом',
            'time': '08:00:00',
            'action': 'Утренняя зарядка',
            'duration': 600,
            'is_pleasant': False,
            'frequency': 1,
            'reward': 'Чашка кофе',
            'is_public': True
        }

    def test_create_habit(self):
        response = self.client.post(
            '/api/habits/', self.habit_data, format='json')
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Error response: {response.data}")  # Выводим детали ошибки
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Habit.objects.count(), 1)
        habit = Habit.objects.first()
        self.assertEqual(habit.action, 'Утренняя зарядка')
        self.assertEqual(habit.duration, 600)

    def test_get_habits_list(self):
        Habit.objects.create(user=self.user, **self.habit_data)
        response = self.client.get('/api/habits/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_update_habit(self):
        habit = Habit.objects.create(user=self.user, **self.habit_data)
        updated_data = self.habit_data.copy()
        updated_data['action'] = 'Вечерняя пробежка'
        response = self.client.put(
            f'/api/habits/{habit.id}/', updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Habit.objects.get(
            id=habit.id).action, 'Вечерняя пробежка')

    def test_delete_habit(self):
        habit = Habit.objects.create(user=self.user, **self.habit_data)
        response = self.client.delete(f'/api/habits/{habit.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Habit.objects.count(), 0)


class TasksTestCase(TestCase):
    @patch('habits.tasks.send_reminder')
    def test_send_habit_reminders(self, mock_send_reminder):
        user = User.objects.create_user(username='testuser', password='12345')
        habit = Habit.objects.create(
            user=user,
            action='Test Habit',
            place='Home',
            time=timezone.now().time(),
            duration=60,
            telegram_chat_id='123456'
        )
        send_habit_reminders()
        mock_send_reminder.assert_called_once_with('123456', 'Test Habit')


class ValidatorsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass')

    def test_validate_related_habit(self):
        pleasant_habit = Habit.objects.create(
            user=self.user, action='Приятная привычка', is_pleasant=True
        )
        habit = Habit(user=self.user, action='Обычная привычка',
                      related_habit=pleasant_habit)
        validate_related_habit(habit)  # Не должно вызывать исключение

        non_pleasant_habit = Habit.objects.create(
            user=self.user, action='Неприятная привычка', is_pleasant=False
        )
        habit.related_habit = non_pleasant_habit
        with self.assertRaises(ValidationError):
            validate_related_habit(habit)

    def test_validate_habit_time(self):
        habit = Habit ( user = self.user,action = 'Тест времени',duration = None )
        validate_habit_time ( habit )  # Не должно вызывать исключение

        habit.duration = 120
        validate_habit_time ( habit )  # Не должно вызывать исключение

        habit.duration = 121
        with self.assertRaises ( ValidationError ):
            validate_habit_time ( habit )

    def test_validate_habit_frequency(self):
        habit = Habit(user=self.user, action='Тест частоты', frequency=7)
        validate_habit_frequency(habit)  # Не должно вызывать исключение

        habit.frequency = 8
        with self.assertRaises(ValidationError):
            validate_habit_frequency(habit)


class PermissionsTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser', password='12345')
        self.habit = Habit.objects.create(
            user=self.user, action='Test Habit', place='Home', time='12:00:00', duration=60)
        self.permission = IsOwnerOrReadOnly()

    def test_has_object_permission(self):
        request = self.factory.get('/')
        request.user = self.user
        self.assertTrue(self.permission.has_object_permission(
            request, None, self.habit))

        other_user = User.objects.create_user(
            username='otheruser', password='12345')
        request.user = other_user
        self.assertFalse(self.permission.has_object_permission(
            request, None, self.habit))


class SerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='12345')
        self.habit_data = {
            'user': self.user,  # Передаем объект пользователя, а не его ID
            'action': 'Test Habit',
            'place': 'Home',
            'time': '12:00:00',
            'duration': 60,
            'is_pleasant': False,
            'frequency': 1,
            'reward': 'Test Reward',
            'is_public': True
        }

    def test_habit_serializer_valid(self):
        serializer = HabitSerializer(data=self.habit_data)
        self.assertTrue(serializer.is_valid())

    def test_habit_serializer_invalid(self):
        invalid_data = self.habit_data.copy()
        invalid_data['duration'] = 121
        serializer = HabitSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('duration', serializer.errors)

    def test_public_habit_serializer(self):
        habit = Habit.objects.create(**self.habit_data)
        serializer = PublicHabitSerializer(habit)
        self.assertEqual(set(serializer.data.keys()), set(
            ['id', 'place', 'time', 'action', 'duration']))


class TelegramBotTestCase(TestCase):
    @patch('habits.telegram_bot.Updater')
    def test_setup_bot(self, mock_updater):
        setup_bot()
        mock_updater.assert_called_once()

    @patch('habits.telegram_bot.setup_bot')
    def test_send_reminder(self, mock_setup_bot):
        mock_bot = Mock()
        mock_setup_bot.return_value.bot = mock_bot
        send_reminder('123456', 'Test Habit')
        mock_bot.send_message.assert_called_once_with(
            chat_id='123456',
            text="Напоминание: Пора выполнить привычку 'Test Habit'!"
        )


class ViewsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', password='12345')
        self.client.force_authenticate(user=self.user)
        self.habit = Habit.objects.create(
            user=self.user,
            action='Test Habit',
            place='Home',
            time='12:00:00',
            duration=60
        )

    def test_list_habits(self):
        response = self.client.get('/api/habits/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_habit(self):
        data = {
            'action': 'New Habit',
            'place': 'Office',
            'time': '09:00:00',
            'duration': 30,
            'is_pleasant': False,
            'frequency': 1,
            'reward': 'Coffee',
            'is_public': True
        }
        response = self.client.post('/api/habits/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Habit.objects.count(), 2)

    def test_retrieve_habit(self):
        response = self.client.get(f'/api/habits/{self.habit.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['action'], 'Test Habit')

    def test_update_habit(self):
        data = {'action': 'Updated Habit'}
        response = self.client.patch(f'/api/habits/{self.habit.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.habit.refresh_from_db()
        self.assertEqual(self.habit.action, 'Updated Habit')

    def test_delete_habit(self):
        response = self.client.delete(f'/api/habits/{self.habit.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Habit.objects.count(), 0)
