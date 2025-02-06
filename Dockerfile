# Используем официальный Python 3.12
FROM python:3.12

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта
COPY . .

# Устанавливаем зависимости
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY . /app/

# Открываем порт для Django
EXPOSE 8000

# Запуск сервера
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
