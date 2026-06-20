# Минимальный официальный образ Python (см. раздел 4.4 отчёта):
# исключает необходимость установки интерпретатора и зависимостей
# на машине пользователя — для запуска продукта достаточно Docker.
FROM python:3.12-slim

WORKDIR /app

# Сначала зависимости отдельным слоем — повторная сборка после
# правки исходного кода не переустанавливает пакеты заново.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Исходный код проекта.
COPY src/ ./src/
COPY tests/ ./tests/

EXPOSE 5000

ENV FLASK_APP=src/server/app.py \
    PYTHONUNBUFFERED=1

CMD ["python3", "-m", "src.server.app"]
