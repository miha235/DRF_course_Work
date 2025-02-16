from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, re_path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger Schema View
schema_view = get_schema_view(
    openapi.Info(
        title="API документация",
        default_version='v1',
        description="Документация для API",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="your_email@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# Простая главная страница


def home(request):
    return HttpResponse("Главная страница работает!")


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/habits/',include ( 'habits.urls' ) ),  # Префикс для приложения habits
    path('api/users/',include ( 'users.urls' ) ),  # Префикс для приложения users
    path('', home, name='home'),  # Главная страница
    re_path(r'^swagger(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger',
         cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc',
         cache_timeout=0), name='schema-redoc'),
]
