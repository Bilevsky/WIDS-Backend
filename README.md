# Проект

WIDS Backend (Wireless Intrusion Detection System) Серверная платформа мониторинга Wi-Fi безопасности

## Стек

- Python 3.11
- FastAPI
- PostgreSQL 16
- Redis
- SQLAlchemy 2.0 (async)
- Alembic
- Docker Compose

## Запустить проект

- Запустить проект: docker compose up --build
- Запустить эмулятор сенсоров: docker compose exec app python emulator/emulator.py

## Применить миграцию

docker compose exec app alembic upgrade head

## После запуска
- API: http://localhost:8000
- Swagger (документация): http://localhost:8000/docs
- Проверка работоспособности: http://localhost:8000/health

## Что реализовано

Сенсоры (sensors)
- CRUD сенсоров с координатами X, Y.
- API-ключ генерируется при создании сенсора и показывается один раз. В базе хранится только SHA-256 хеш.
- POST /sensors/{id}/rotate-key выдаёт новый ключ.
- GET /sensors/me проверяет ключ, который передаётся в заголовке X-API-Key.

Белый список (whitelist)
- /whitelist/aps: легитимные точки доступа (SSID + MAC + тип шифрования).
- /whitelist/devices: корпоративные устройства (MAC).
- MAC-адреса автоматически приводятся к формату AA:BB:CC:DD:EE:FF.

Приём телеметрии и эмулятор
- POST /telemetry/batch: пакетный приём до 500 событий за запрос, валидация, запись в БД одной командой.
- Сенсор определяется по API-ключу, а не по полю в теле запроса, поэтому подписаться чужим именем нельзя.
- Rate limiting через Redis: лимит запросов на сенсор в минуту, при превышении ответ 429.
- Эмулятор сенсоров: три виртуальных сенсора в отдельных потоках, уровень сигнала (RSSI) считается по расстоянию до источника.