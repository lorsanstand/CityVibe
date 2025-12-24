# 🤝 Contributing to CityVibe

Спасибо за интерес к контрибьютингу в CityVibe! Этот документ описывает процесс и рекомендации для разработчиков.

## 📋 Содержание

- [Код поведения](#код-поведения)
- [Как начать](#как-начать)
- [Процесс разработки](#процесс-разработки)
- [Стиль кода](#стиль-кода)
- [Создание Pull Request](#создание-pull-request)
- [Тестирование](#тестирование)

---

## 📝 Код поведения

Мы придерживаемся Contributor Covenant Code of Conduct. Ожидается, что все участники проекта будут соблюдать эти стандарты поведения:

- ✅ Будьте уважительны к другим участникам
- ✅ Приветствуйте различные точки зрения
- ✅ Критикуйте идеи, а не людей
- ✅ Помогайте друг другу расти

Любые нарушения можно сообщить в модераторам проекта.

---

## 🚀 Как начать

### 1. Форк и клонирование

```bash
# Форкните репозиторий на GitHub
# Затем клонируйте свой форк
git clone https://github.com/YOUR-USERNAME/CityVibe.git
cd CityVibe

# Добавьте upstream
git remote add upstream https://github.com/lorsanstand/CityVibe.git
```

### 2. Создание ветки

```bash
# Получите последние изменения
git fetch upstream
git checkout upstream/realese/main

# Создайте feature ветку
git checkout -b feature/your-feature-name

# Или для bug fix
git checkout -b fix/your-bug-fix
```

### 3. Настройка окружения разработки

```bash
# Создайте виртуальное окружение
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Установите зависимости
pip install -r requirements.txt
pip install -e .

# Или используйте Poetry
poetry install

# Создайте .env файл
cp .env.example .env
# Отредактируйте .env для вашего окружения
```

### 4. Запуск приложения

```bash
# Запустите Docker контейнеры (БД, RabbitMQ)
docker-compose up -d database rabbitmq

# Запустите миграции
alembic upgrade head

# Запустите сервер
python -m app.main

# В другом терминале запустите Celery worker
celery -A app.celery_app worker -l info
```

---

## 🔧 Процесс разработки

### Коммит сообщения

Используйте семантические коммит сообщения:

```bash
# Format
<type>(<scope>): <subject>

# Examples
git commit -m "feat(auth): add email verification"
git commit -m "fix(events): fix search filtering"
git commit -m "docs(readme): update installation instructions"
git commit -m "refactor(users): improve user service logic"
git commit -m "test(events): add tests for event creation"
```

### Типы коммитов:
- **feat**: новая функциональность
- **fix**: исправление ошибки
- **docs**: изменения документации
- **style**: форматирование кода (не функциональные изменения)
- **refactor**: переписывание кода без изменения функциональности
- **test**: добавление или обновление тестов
- **chore**: изменения в build процессе, зависимостях
- **perf**: улучшение производительности

### Ветки

Используйте следующие соглашения для веток:

```bash
# Features
feature/add-notifications
feature/improve-search-algorithm

# Bug fixes
fix/login-issue
fix/photo-upload-error

# Documentation
docs/api-endpoints
docs/setup-guide

# Refactoring
refactor/user-service
refactor/event-validation
```

---

## 🎨 Стиль кода

### Python стиль (PEP 8)

```bash
# Установите linters
pip install pylint flake8 black isort

# Форматируйте код
black backend/app

# Сортируйте импорты
isort backend/app

# Проверьте стиль
flake8 backend/app
pylint backend/app
```

### Соглашения именования

```python
# Функции и методы: snake_case
def get_user_by_id():
    pass

# Классы: PascalCase
class UserService:
    pass

# Константы: UPPER_SNAKE_CASE
MAX_PHOTO_SIZE = 15 * 1024 * 1024

# Приватные: _leading_underscore
def _internal_helper():
    pass

# Для Pydantic моделей используйте descriptive names
class UserCreate(BaseModel):
    email: str
    username: str
```

### Тип аннотации

Всегда используйте type hints:

```python
from typing import Optional, List
from app.users.models import UserModel

def get_user(user_id: str) -> Optional[UserModel]:
    """Get user by ID."""
    pass

def get_users(offset: int = 0, limit: int = 10) -> List[UserModel]:
    """Get list of users."""
    pass
```

### Docstrings

Используйте Google-style docstrings:

```python
def create_event(event_data: EventCreate, user_id: UUID) -> Event:
    """Create a new event.
    
    Args:
        event_data: Event creation data
        user_id: ID of the user creating the event
        
    Returns:
        Created event object
        
    Raises:
        HTTPException: If event already exists
        
    Example:
        >>> event = await create_event(event_data, user_id)
        >>> print(event.id)
    """
    pass
```

---

## 🧪 Тестирование

### Написание тестов

```bash
# Все тесты должны быть в backend/tests/
# Структура должна соответствовать структуре app/

backend/
  app/
    auth/
  tests/
    auth/
      test_service.py
      test_router.py
      test_models.py
```

### Пример теста

```python
import pytest
from httpx import AsyncClient
from app.users.models import UserModel

@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration."""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "secure_password_123"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_existing_user(client: AsyncClient, user: UserModel):
    """Test registration with existing email."""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": user.email,
            "username": "anotheruser",
            "password": "secure_password_123"
        }
    )
    
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]
```

### Запуск тестов

```bash
# Все тесты
pytest backend/tests/

# С покрытием
pytest backend/tests/ --cov=app --cov-report=html

# Конкретный файл
pytest backend/tests/test_auth.py

# Конкретный тест
pytest backend/tests/test_auth.py::test_register_user

# С verbose выводом
pytest backend/tests/ -v

# Останавливать на первой ошибке
pytest backend/tests/ -x
```

### Требования к тестам

- Покрытие должно быть не менее **80%**
- Все новые функции должны иметь тесты
- Тесты должны быть независимыми и можно запускать в любом порядке
- Используйте fixtures для общего setup

---

## 📝 Создание Pull Request

### Шаг 1: Подготовка

```bash
# Убедитесь, что код соответствует стилю
black backend/app
isort backend/app
flake8 backend/app

# Запустите тесты
pytest backend/tests/

# Обновите документацию если нужно
# Добавьте логирование где необходимо
```

### Шаг 2: Коммиты

```bash
# Делайте atomic commits
git add app/auth/service.py
git commit -m "feat(auth): implement password reset"

git add app/auth/router.py
git commit -m "feat(auth): add password reset endpoint"

git add tests/test_auth.py
git commit -m "test(auth): add password reset tests"

# Синхронизируйте с upstream
git fetch upstream
git rebase upstream/realese/main
```

### Шаг 3: Push и Pull Request

```bash
# Push в ваш форк
git push origin feature/your-feature-name

# Откройте PR на GitHub
# https://github.com/lorsanstand/CityVibe/pull/new/realese/main
```

### Шаблон PR Description

```markdown
## 📝 Description
Brief description of what this PR does

## 🎯 Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Refactoring

## 🔗 Related Issues
Closes #123

## ✅ Checklist
- [ ] Code follows project style guidelines
- [ ] Tests are added/updated
- [ ] Documentation is updated
- [ ] No new warnings generated
- [ ] All tests pass locally

## 📸 Screenshots
If applicable, add screenshots showing the changes

## 🔍 Testing
Describe how to test these changes:
1. Start the app
2. Navigate to...
3. Verify...
```

### Что проверяется в PR:

- ✅ Стиль кода (flake8, black)
- ✅ Тесты (pytest)
- ✅ Type checking (mypy)
- ✅ Покрытие (>80%)
- ✅ Документация

---

## 📚 Полезные ресурсы

### Документация
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [AsyncIO Guide](https://docs.python.org/3/library/asyncio.html)

### Tools
- [Black Code Formatter](https://github.com/psf/black)
- [Pytest](https://docs.pytest.org/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)
- [Celery Documentation](https://docs.celeryproject.io/)

### Community
- [FastAPI Discord](https://discord.gg/VQjSZaeJmf)
- [Python Discord](https://discord.gg/python)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/fastapi)

---

## ❓ FAQ

### Q: Как я могу начать помогать проекту?
A: Начните с issues помеченных как `good-first-issue` или `help-wanted`

### Q: Должны ли мои commits быть squashed?
A: Нет, мы предпочитаем atomic commits. Мейнтейнеры отреагируют если нужны изменения.

### Q: Как долго ждать ревью PR?
A: Обычно 2-7 дней в зависимости от сложности

### Q: Что если мой PR будет отклонен?
A: Это нормально! Получите feedback и попробуйте еще раз

### Q: Могу ли я работать над несколькими features одновременно?
A: Используйте отдельные ветки для каждой feature

---

## 🎓 Дополнительно

### Коммит очистка

```bash
# Если нужно переписать последние commits
git rebase -i HEAD~3

# Обновить commit message
git commit --amend -m "new message"

# Добавить файлы в последний commit
git add .
git commit --amend --no-edit
```

### Синхронизация форка

```bash
# Получить последние изменения из upstream
git fetch upstream

# Переместить вашу ветку на последний upstream/realese/main
git rebase upstream/realese/main

# Если есть конфликты, разрешите их и продолжите
git rebase --continue
```

---

**Спасибо за вклад в CityVibe! 🚀**

Если у вас есть вопросы, создайте issue или свяжитесь с мейнтейнерами.
