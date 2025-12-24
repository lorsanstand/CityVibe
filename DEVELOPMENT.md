# 🛠️ Development Guide

Подробное руководство для разработки CityVibe

## 📋 Содержание

- [Локальная настройка](#локальная-настройка)
- [Структура кода](#структура-кода)
- [Добавление новой функции](#добавление-новой-функции)
- [Работа с БД](#работа-с-бд)
- [Отладка](#отладка)
- [Performance](#performance)

---

## 🖥️ Локальная настройка

### Требования

```bash
# Python версия
python --version  # >= 3.13

# Docker (опционально, но рекомендуется)
docker --version
docker-compose --version
```

### Полная установка с Docker

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/lorsanstand/CityVibe.git
cd CityVibe

# 2. Создайте .env файл
cp .env.example .env

# 3. Запустите все сервисы
docker-compose up -d

# 4. Проверьте логи
docker-compose logs -f backend

# 5. Приложение доступно на http://localhost:8000
```

### Локальная установка (без Docker)

```bash
# 1. Установите PostgreSQL и RabbitMQ
# На macOS:
brew install postgresql rabbitmq

# На Ubuntu:
sudo apt-get install postgresql postgresql-contrib rabbitmq-server

# 2. Создайте БД
createdb cityvibe_db
createdb cityvibe_test

# 3. Настройте .env файл
# Обновите DB_HOST, RMQ_HOST и т.д. на localhost

# 4. Создайте виртуальное окружение
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 5. Установите зависимости
pip install -r requirements.txt
# или
poetry install

# 6. Запустите миграции
alembic upgrade head

# 7. Запустите приложение
python -m app.main

# 8. В другом терминале запустите Celery
celery -A app.celery_app worker -l info
```

### IDE Setup

#### VSCode

```json
// .vscode/settings.json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.python",
    "editor.formatOnSave": true
  },
  "python.testing.pytestEnabled": true,
  "python.testing.pytestPath": "pytest"
}
```

#### PyCharm

1. Откройте Settings → Project → Python Interpreter
2. Выберите виртуальное окружение из `backend/venv`
3. Установите черный форматер:
   - Settings → Tools → Python Integrated Tools
   - Default test runner: pytest

---

## 📁 Структура кода

### Архитектура

```
app/
├── auth/              # Аутентификация
│   ├── router.py      # API endpoints
│   ├── service.py     # Бизнес-логика
│   ├── models.py      # ORM модели
│   ├── schemas.py     # Pydantic validation
│   ├── dao.py         # Data access objects
│   ├── dependencies.py# Dependency injection
│   └── utils.py       # Helper функции
```

### Паттерны

Приложение использует **3-слойную архитектуру**:

```
Request → Router (endpoints) 
    ↓
Service (бизнес-логика)
    ↓
DAO/Repository (работа с БД)
    ↓
Database
```

#### Пример: Создание пользователя

```
1. POST /api/auth/register
   └─ router.py::register()

2. AuthService.register_new_user()
   └─ service.py (валидация, логирование)

3. UserDao.add()
   └─ base_dao.py (SQL запрос)

4. PostgreSQL
   └─ таблица users
```

### Зависимости

```python
# Использование dependency injection для текущего пользователя
from app.auth.dependencies import get_current_active_user

@router.get("/me")
async def get_profile(user: UserModel = Depends(get_current_active_user)):
    return user

# Автоматическая проверка JWT токена в headers
```

---

## ✨ Добавление новой функции

### Пример: Добавить функцию "нравится" (Like) для события

#### 1. Создайте модель

```python
# app/events/models.py
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import uuid

class EventLike(Base):
    __tablename__ = "event_likes"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # Relationships
    user: Mapped[UserModel] = relationship("UserModel")
    event: Mapped[EventModel] = relationship("EventModel")
    
    __table_args__ = (
        UniqueConstraint("user_id", "event_id", name="uq_user_event_like"),
    )
```

#### 2. Создайте Pydantic schema

```python
# app/events/schemas.py
from pydantic import BaseModel
import uuid

class EventLikeCreate(BaseModel):
    event_id: uuid.UUID

class EventLike(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    event_id: uuid.UUID
    created_at: datetime
    
    class Config:
        from_attributes = True
```

#### 3. Создайте DAO

```python
# app/events/dao.py
from app.base_dao import BaseDAO
from app.events.models import EventLike
from app.events.schemas import EventLikeCreate

class EventLikeDao(BaseDAO[EventLike, EventLikeCreate, dict]):
    model = EventLike
```

#### 4. Создайте сервис

```python
# app/events/service.py
class EventLikeService:
    @classmethod
    async def add_like(cls, user_id: uuid.UUID, event_id: uuid.UUID) -> EventLike:
        async with async_session_maker() as session:
            # Проверка существования
            existing = await EventLikeDao.find_one_or_none(
                session, 
                user_id=user_id, 
                event_id=event_id
            )
            
            if existing:
                raise HTTPException(status.HTTP_409_CONFLICT, "Already liked")
            
            # Проверка события
            event = await EventDao.find_one_or_none(session, id=event_id)
            if not event:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Event not found")
            
            # Создание
            like = await EventLikeDao.add(
                session,
                {"user_id": user_id, "event_id": event_id}
            )
            await session.commit()
            
            log.info("Event liked", extra={"user_id": str(user_id), "event_id": str(event_id)})
            return like
    
    @classmethod
    async def remove_like(cls, user_id: uuid.UUID, event_id: uuid.UUID):
        async with async_session_maker() as session:
            await EventLikeDao.delete(
                session,
                user_id=user_id,
                event_id=event_id
            )
            await session.commit()
            log.info("Event unlike", extra={"user_id": str(user_id), "event_id": str(event_id)})
```

#### 5. Создайте роутеры

```python
# app/events/router.py
@router.post("/{event_id}/like")
async def like_event(
    event_id: uuid.UUID,
    user: UserModel = Depends(get_current_active_user)
) -> dict:
    await EventLikeService.add_like(user.id, event_id)
    log.info("Event like endpoint called", extra={"user_id": str(user.id), "event_id": str(event_id)})
    return {"message": "Event liked"}

@router.delete("/{event_id}/like")
async def unlike_event(
    event_id: uuid.UUID,
    user: UserModel = Depends(get_current_active_user)
) -> dict:
    await EventLikeService.remove_like(user.id, event_id)
    log.info("Event unlike endpoint called", extra={"user_id": str(user.id), "event_id": str(event_id)})
    return {"message": "Event unliked"}
```

#### 6. Создайте тесты

```python
# backend/tests/test_event_likes.py
import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_like_event(client: AsyncClient, user: UserModel, event: EventModel, token: str):
    """Test liking an event"""
    response = await client.post(
        f"/api/events/{event.id}/like",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert response.json()["message"] == "Event liked"

@pytest.mark.asyncio
async def test_unlike_event(client: AsyncClient, user: UserModel, event: EventModel, token: str):
    """Test unliking an event"""
    # First like
    await client.post(
        f"/api/events/{event.id}/like",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Then unlike
    response = await client.delete(
        f"/api/events/{event.id}/like",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert response.json()["message"] == "Event unliked"

@pytest.mark.asyncio
async def test_like_twice_fails(client: AsyncClient, user: UserModel, event: EventModel, token: str):
    """Test that liking twice fails"""
    await client.post(
        f"/api/events/{event.id}/like",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    response = await client.post(
        f"/api/events/{event.id}/like",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 409
```

#### 7. Создайте миграцию БД

```bash
# Создайте миграцию
alembic revision --autogenerate -m "Add event_likes table"

# Примените миграцию
alembic upgrade head
```

---

## 🗄️ Работа с БД

### Миграции

```bash
# Создать новую миграцию (автоматическая)
alembic revision --autogenerate -m "Add new column"

# Создать пустую миграцию (вручную)
alembic revision -m "Custom migration"

# Применить все новые миграции
alembic upgrade head

# Откатить последнюю миграцию
alembic downgrade -1

# Откатить все
alembic downgrade base

# Показать статус миграций
alembic current
```

### Запросы к БД

```python
# Асинхронные запросы
async with async_session_maker() as session:
    # SELECT
    stmt = select(User).where(User.email == "test@example.com")
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    # INSERT
    user = User(email="test@example.com")
    session.add(user)
    await session.commit()
    
    # UPDATE
    await session.execute(
        update(User).where(User.id == user_id).values(name="New Name")
    )
    await session.commit()
    
    # DELETE
    await session.execute(delete(User).where(User.id == user_id))
    await session.commit()
```

### Оптимизация

```python
# Используйте select() вместо filter
# ❌ Неправильно
user = await session.query(User).filter(User.id == user_id).first()

# ✅ Правильно
stmt = select(User).where(User.id == user_id)
user = await session.execute(stmt)

# Загрузка связей
from sqlalchemy.orm import selectinload

stmt = select(User).options(selectinload(User.events))
result = await session.execute(stmt)
users = result.scalars().all()
```

---

## 🐛 Отладка

### Логирование

```python
import logging

log = logging.getLogger(__name__)

# INFO - основные события
log.info("User registered", extra={"user_id": str(user.id), "email": user.email})

# DEBUG - детальная информация
log.debug("Processing payment", extra={"order_id": str(order_id), "amount": amount})

# WARNING - потенциальные проблемы
log.warning("Rate limit exceeded", extra={"user_id": str(user_id), "limit": 100})

# ERROR - ошибки
log.error(f"Payment failed: {str(e)}", extra={"order_id": str(order_id)})
```

### Просмотр логов

```bash
# Последние логи
docker-compose logs -f backend

# Логи определенного сервиса
docker-compose logs -f database

# Фильтрация
docker-compose logs backend | grep "ERROR"
```

### Отладка в PyCharm

1. Установите breakpoint: `Ctrl+Shift+F8`
2. Запустите debug: `Shift+F9`
3. Используйте console: `Alt+F9`

### Отладка в VSCode

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "app.main",
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend"
      },
      "console": "integratedTerminal"
    }
  ]
}
```

---

## ⚡ Performance

### Оптимизация запросов

```python
# ❌ N+1 проблема
for event in events:
    event.author = await UserDao.find_one_or_none(id=event.user_id)

# ✅ Правильный способ с join
from sqlalchemy.orm import selectinload
stmt = select(Event).options(selectinload(Event.author))
```

### Кэширование

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_event_config():
    """Кэшировать конфигурацию события"""
    return {"max_capacity": 1000, "max_photos": 10}
```

### Асинхронность

```python
# ❌ Синхронный вызов блокирует
for user in users:
    await send_email(user.email)

# ✅ Используйте gather для параллельных операций
import asyncio
await asyncio.gather(*[send_email(user.email) for user in users])
```

### Batch операции

```python
# Вставка большого количества данных
from sqlalchemy import insert

values = [
    {"user_id": user_id, "event_id": event_id}
    for user_id, event_id in data
]

await session.execute(insert(EventLike).values(values))
await session.commit()
```

---

## 📊 Мониторинг

### Health checks

```bash
# Проверка БД
curl http://localhost:8000/api/health/db

# Проверка RabbitMQ
curl http://localhost:8000/api/health/rabbitmq

# Общее здоровье
curl http://localhost:8000/api/health
```

### Метрики

```bash
# CPU и память
docker stats backend

# Размер БД
docker exec cityvibe-database psql -U cityvibe_user -d cityvibe_db -c "SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname)) FROM pg_database;"
```

---

**Happy coding! 🚀**
