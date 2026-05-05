# Дипломный проект (базовая часть)

Backend для сервиса автоматизации закупок на Django и Django Rest Framework.

На этом этапе выполнены:

- Этап 1: создание и настройка проекта;
- Этап 2: проработка моделей данных;
- Этап 3: импорт каталога товаров из YAML;
- Этап 4: API (вход, регистрация, товары, корзина, контакты, заказ, письма, список и детали заказов, статус заказа для магазина);
- Этап 5: сценарий пользователя — регистрация с письмом, корзина, адрес, подтверждение заказа, письмо о заказе, просмотр заказов.

## Требования

- Python 3.10+
- pip

## Запуск проекта

1. Создать виртуальное окружение:

```bash
python3 -m venv venv
```

2. Активировать окружение:

```bash
source venv/bin/activate
```

3. Установить зависимости:

```bash
pip install -r requirements.txt
```

4. Применить миграции:

```bash
python manage.py migrate
```

5. Создать суперпользователя:

```bash
python manage.py createsuperuser
```

6. Запустить сервер:

```bash
python manage.py runserver
```

Документация API (OpenAPI 3, [drf-spectacular](https://drf-spectacular.readthedocs.io/en/latest/readme.html)):

- JSON-схема: http://127.0.0.1:8000/api/schema/
- **Swagger UI** (удобно смотреть поля и пробовать запросы): http://127.0.0.1:8000/api/schema/swagger-ui/
- ReDoc: http://127.0.0.1:8000/api/schema/redoc/

В Swagger для методов с токеном нажми **Authorize** и введи: `Token <твой_ключ>`.

7. Фоновые задачи (Celery): письма при регистрации и подтверждении заказа уходят в очередь. Нужны **Redis** и воркер:

```bash
# Терминал 1 — брокер (macOS: brew install redis && redis-server)
redis-server

# Терминал 2 — воркер
celery -A orders worker -l info
```

Переменные окружения (по желанию): `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` (по умолчанию `redis://127.0.0.1:6379/0`).

## Throttling

Чтобы не долбили регистрацию/логин/оформление заказа тысячу раз в секунду, на этих ручках висят лимиты (`SettingsScopedThrottle` + `DEFAULT_THROTTLE_RATES` в `orders/settings.py`). Проверка: `python manage.py test backend.tests`.

## OAuth (Google и GitHub)

Ставим ключи в переменные окружения: `SOCIAL_AUTH_GOOGLE_OAUTH2_KEY`, `SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET`, при желании `SOCIAL_AUTH_GITHUB_KEY`, `SOCIAL_AUTH_GITHUB_SECRET`. В консоли разработчика в redirect URI указать что-то вроде `http://127.0.0.1:8000/oauth/complete/google-oauth2/` (для github — тот же хост, путь `/oauth/complete/github/`).

В браузере: `http://127.0.0.1:8000/oauth/login/google-oauth2/` — после удачного входа кинет на `http://127.0.0.1:8000/api/v1/auth/social/token/`, там JSON с `token` как после обычного логина.

Если глючит редирект: в админке **Sites** поменять домен с `example.com` на `127.0.0.1:8000`.

## Что сделано по моделям (этап 2)

Добавлены модели:

- `User` (кастомная авторизация по email),
- `Shop`,
- `Category`,
- `Product`,
- `ProductInfo`,
- `Parameter`,
- `ProductParameter`,
- `Contact`,
- `Order`,
- `OrderItem`.

Также все модели зарегистрированы в админке.

## Импорт каталога (этап 3)

Пример импорта из файла:

```bash
python manage.py import_catalog --file data/shop1.yaml
```

После выполнения команды товары, категории и характеристики будут загружены в базу.
