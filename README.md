# Дипломный проект (базовая часть)

Backend для сервиса автоматизации закупок на Django и Django REST Framework.

На этом этапе выполнены:
- Этап 1: создание и настройка проекта;
- Этап 2: проработка моделей данных.

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
