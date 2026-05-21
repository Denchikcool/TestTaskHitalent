# TestTaskHitalent
Тестовое задание: API организационной структуры
REST API для управления организационной структурой компании: подразделения и сотрудники.

## Стек

- **FastAPI** + **SQLAlchemy 2.0** (async) + **PostgreSQL**
- **Alembic** — миграции
- **Docker** + **docker-compose**
- **pytest** + **pytest-asyncio**

## Запуск

```bash
git clone https://github.com/Denchikcool/TestTaskHitalent.git
cd TestTaskHitalent
docker-compose up --build
```
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health: http://localhost:8000/health

Миграции применяются автоматически перед стартом приложения.

## Локальный запуск без Docker

```bash
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt

export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/org_db
alembic upgrade head
uvicorn app.main:app --reload
```

## Тесты

Используют SQLite in-memory, PostgreSQL не нужен:

```bash
pip install -r requirements.txt
pytest -v
```

## Структура

```
app/
├── config.py          # настройки из env
├── database.py        # async engine и сессия
├── models.py          # ORM модели (Department, Employee)
├── schemas.py         # Pydantic схемы
├── main.py            # FastAPI app
└── routers/
    └── departments.py # все эндпоинты
alembic/versions/
    001_initial.py     # создание таблиц
    002_unique_name.py # уникальность имён
tests/
    test_departments.py
```

## Эндпоинты

|   Метод  |                         URL                       |             Описание            |
|----------|---------------------------------------------------|---------------------------------|
| `POST`   |             `/api/v1/departments/`                |      Создать подразделение      |
| `GET`    |             `/api/v1/departments/{id}`            | Получить подразделение + дерево |
| `PATCH`  |             `/api/v1/departments/{id}`            |    Переименовать/переместить    |
| `DELETE` | `/api/v1/departments/{id}?mode=cascade\|reassign` |             Удалить             |
| `POST`   |         `/api/v1/departments/{id}/employees/`     |        Добавить сотрудника      |