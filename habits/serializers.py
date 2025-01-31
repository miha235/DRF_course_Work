from rest_framework import serializers
from .models import Habit


class HabitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Habit
        fields = ['id', 'user', 'place', 'time', 'action', 'is_pleasant', 'related_habit',
                  'frequency', 'reward', 'duration', 'is_public']
        read_only_fields = ['user']

    def validate(self, data):
        if data.get('is_pleasant'):
            if data.get('related_habit') or data.get('reward'):
                raise serializers.ValidationError(
                    "Приятная привычка не может иметь связанную привычку или вознаграждение.")
        elif not data.get('related_habit') and not data.get('reward'):
            raise serializers.ValidationError(
                "Привычка должна иметь связанную привычку или вознаграждение.")

        if data.get('duration'):
            if data['duration'] > 120:
                raise serializers.ValidationError(
                    "Длительность привычки не может превышать 120 секунд.")
            if data['duration'] < 1:
                raise serializers.ValidationError(
                    "Длительность привычки должна быть положительным числом.")

        if data.get('frequency'):
            if data['frequency'] > 7:
                raise serializers.ValidationError(
                    "Нельзя выполнять привычку реже, чем раз в 7 дней.")
            if data['frequency'] < 1:
                raise serializers.ValidationError(
                    "Частота выполнения должна быть положительным числом.")

        if data.get('related_habit') and not data['related_habit'].is_pleasant:
            raise serializers.ValidationError(
                "Связанная привычка должна быть приятной.")

        return data


class PublicHabitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Habit
        fields = ['id', 'place', 'time', 'action', 'duration']
