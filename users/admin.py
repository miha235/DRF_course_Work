from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser  # Импортируй свою модель пользователя

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('username', 'email')
