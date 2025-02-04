from datetime import time
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.core.exceptions import ValidationError
from unittest.mock import patch
from .models import Habit
from .tasks import send_habit_reminders
from .validators import validate_related_habit, validate_habit_time, validate_habit_frequency


class HabitModelTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')

    def test_habit_str(self):
        habit = Habit.objects.create(user=self.user, action="Утренняя зарядка", place="Дом", time=time(8, 0),
                                     duration=60)
        self.assertEqual(str(habit), "Утренняя зарядка в 08:00:00 в Дом")

    def test_habit_ordering(self):
        h1 = Habit.objects.create(user=self.user, action="Ранний подъем", time=time(6, 0), duration=60)
        h2 = Habit.objects.create(user=self.user, action="Зарядка", time=time(7, 0), duration=60)
        habits = Habit.objects.all()
        self.assertEqual(habits[0], h1)
        self.assertEqual(habits[1], h2)

    def test_habit_reward_validation(self):
        habit = Habit(user=self.user, action="Приятная привычка", is_pleasant=True, reward="Шоколадка")
        with self.assertRaises(ValidationError):
            habit.full_clean()


class HabitAPITestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')
        self.other_user = get_user_model().objects.create_user(username='otheruser', password='testpass')
        self.client.force_authenticate(user=self.user)

        self.habit_data = {
            'place': 'Дом',
            "time": time(0, 10),
            'action': 'Утренняя зарядка',
            'duration': 60,
            'frequency': 1,
            'reward': 'Чашка кофе',
            'is_public': True
        }

    def test_create_habit(self):
        # Преобразуем время в строку
        self.habit_data['time'] = self.habit_data['time'].strftime('%H:%M:%S')
        response = self.client.post('/api/habits/', self.habit_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Habit.objects.count(), 1)

    def test_create_habit_without_auth(self):
        self.client.logout()
        response = self.client.post('/api/habits/', self.habit_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_habits(self):
        Habit.objects.create(user=self.user, **self.habit_data)
        response = self.client.get('/api/habits/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_cannot_get_other_users_habits(self):
        Habit.objects.create(user=self.other_user, **self.habit_data)
        response = self.client.get('/api/habits/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_update_habit(self):
        habit = Habit.objects.create(user=self.user, **self.habit_data)
        updated_data = self.habit_data.copy()
        updated_data['duration'] = 120

        response = self.client.put(f'/api/habits/{habit.id}/', updated_data, format='json')
        print(f"Response: {response.status_code}, {response.data}")  # Логируем ответ для отладки
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        habit.refresh_from_db()
        self.assertEqual(habit.duration, 120)

    def test_cannot_update_other_users_habit(self):
        habit = Habit.objects.create(user=self.other_user, **self.habit_data)
        response = self.client.put(f'/api/habits/{habit.id}/', self.habit_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_habit(self):
        habit = Habit.objects.create(user=self.user, **self.habit_data)
        response = self.client.delete(f'/api/habits/{habit.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Habit.objects.count(), 0)

    def test_cannot_delete_other_users_habit(self):
        habit = Habit.objects.create(user=self.other_user, **self.habit_data)
        response = self.client.delete(f'/api/habits/{habit.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_public_habits(self):
        Habit.objects.create(user=self.user, **self.habit_data)
        response = self.client.get('/api/public-habits/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class TasksTestCase(TestCase):
    @patch('habits.tasks.send_reminder')
    def test_send_habit_reminders(self, mock_send_reminder):
        user = get_user_model().objects.create_user(username='testuser', password='12345')
        Habit.objects.create(user=user, action='Test Habit', place='Home', time=timezone.now().time(),
                             duration=60, telegram_chat_id='123456')
        send_habit_reminders()
        mock_send_reminder.assert_called_once()


class ValidatorsTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')

    def test_validate_related_habit(self):
        pleasant_habit = Habit.objects.create(user=self.user, action='Приятная привычка', is_pleasant=True)
        habit = Habit(user=self.user, action='Обычная привычка', related_habit=pleasant_habit)
        validate_related_habit(habit)

        non_pleasant_habit = Habit.objects.create(user=self.user, action='Неприятная привычка', is_pleasant=False)
        habit.related_habit = non_pleasant_habit
        with self.assertRaises(ValidationError):
            validate_related_habit(habit)

    def test_validate_habit_time(self):
        habit = Habit(user=self.user, action='Тест времени', duration=120)
        try:
            habit.full_clean()  # Проверка на валидность
        except ValidationError as e:
            self.fail(f"Validation failed with error: {e}")

        habit.duration = 121
        try:
            habit.full_clean()  # Проверка на ошибку валидации
            self.fail("ValidationError expected")  # Ошибка должна быть
        except ValidationError:
            pass  # Это правильно

    def test_validate_habit_frequency(self):
        habit = Habit(user=self.user, action='Тест частоты', frequency=7)
        try:
            validate_habit_frequency(habit)  # Эта проверка должна пройти
        except ValidationError as e:
            self.fail(f"Validation failed with error: {e}")

        habit.frequency = 8
        try:
            validate_habit_frequency(habit)
            self.fail("ValidationError expected")  # Ошибка должна быть
        except ValidationError:
            pass


