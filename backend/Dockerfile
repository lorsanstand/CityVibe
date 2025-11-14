FROM python:3.13.7-bookworm

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY .env .

COPY alembic.ini .

COPY app/ ./app

CMD ["python", "-m", "app.main"]