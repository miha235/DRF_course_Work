# habits/views.py
from rest_framework import viewsets, permissions
from rest_framework.pagination import PageNumberPagination
from .models import Habit
from .serializers import HabitSerializer, PublicHabitSerializer
from .permissions import IsOwnerOrReadOnly
from .telegram_bot import send_reminder


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100


class HabitViewSet(viewsets.ModelViewSet):
    serializer_class = HabitSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # Возвращаем пустой queryset для генерации схемы
            return Habit.objects.none()
        return Habit.objects.select_related('user').filter(user=self.request.user)

    def perform_create(self, serializer):
        habit = serializer.save(user=self.request.user)
        telegram_chat_id = habit.user.telegram_chat_id  # Получаем chat_id через пользователя
        if telegram_chat_id:
            send_reminder(telegram_chat_id, habit.action)


class PublicHabitViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PublicHabitSerializer
    queryset = Habit.objects.filter(is_public=True)
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination
