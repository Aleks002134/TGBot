# Задает базовый образ
FROM python:3.10

# Устанавливает рабочую директорию в контейнере
WORKDIR /app
# Копирует requirements.txt в контейнер
COPY requirements.txt .

# Устанавливает зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копирует содержимое текущей директории в контейнер
COPY . .

# Запускает приложение при старте контейнера
CMD [ "python", "main.py" ]
