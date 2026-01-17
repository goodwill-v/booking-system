# PostgreSQL Driver

Модуль-драйвер для удобной работы с PostgreSQL базой данных. Предоставляет простой и интуитивный интерфейс для выполнения CRUD операций.

## Установка

```bash
pip install -r requirements.txt
```

## Настройка

Создайте файл `.env` в корне проекта со следующими параметрами:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_password
```

## Быстрый старт

### Базовое использование

```python
from postgres_driver import PostgreSQLDriver

# Создаем экземпляр драйвера
db = PostgreSQLDriver()

# Подключаемся
db.connect()

# CREATE - Вставка записи
new_id = db.create(
    table='users',
    data={'name': 'Иван', 'email': 'ivan@example.com', 'age': 30},
    returning='id'
)

# READ - Чтение записей
users = db.read(table='users')
user = db.read_by_id(table='users', id_value=new_id)

# UPDATE - Обновление записи
db.update_by_id(
    table='users',
    id_value=new_id,
    data={'age': 31}
)

# DELETE - Удаление записи
db.delete_by_id(table='users', id_value=new_id)

# Закрываем соединение
db.disconnect()
```

### Использование с контекстным менеджером

```python
with PostgreSQLDriver() as db:
    # Автоматическое подключение и отключение
    users = db.read(table='users', where={'age': 30})
    count = db.count(table='users')
```

## API Документация

### Инициализация

```python
PostgreSQLDriver(
    host=None,           # Хост (по умолчанию из DB_HOST)
    port=None,           # Порт (по умолчанию из DB_PORT)
    database=None,       # База данных (по умолчанию из DB_NAME)
    user=None,           # Пользователь (по умолчанию из DB_USER)
    password=None,       # Пароль (по умолчанию из DB_PASSWORD)
    use_pool=False,      # Использовать пул соединений
    pool_minconn=1,      # Минимум соединений в пуле
    pool_maxconn=10      # Максимум соединений в пуле
)
```

### Управление соединением

#### `connect()`
Устанавливает соединение с базой данных. Вызывается автоматически при использовании контекстного менеджера.

**Возвращает:** True при успешном подключении

**Вызывает:** `ConnectionError` при ошибке подключения

#### `disconnect()`
Закрывает соединение с базой данных. Вызывается автоматически при выходе из контекстного менеджера.

### CREATE методы

#### `create(table, data, returning=None)`
Вставляет одну запись в таблицу.

**Параметры:**
- `table` (str): Имя таблицы
- `data` (dict): Словарь с данными (ключ - колонка, значение - значение)
- `returning` (str, optional): Колонка для возврата после вставки

**Возвращает:** Значение возвращаемой колонки или None

**Пример:**
```python
id = db.create(
    table='users',
    data={'name': 'Иван', 'email': 'ivan@example.com'},
    returning='id'
)
```

#### `create_many(table, data_list, returning=None)`
Вставляет несколько записей в таблицу.

**Параметры:**
- `table` (str): Имя таблицы
- `data_list` (list): Список словарей с данными
- `returning` (str, optional): Колонка для возврата

**Возвращает:** Список значений возвращаемой колонки

**Пример:**
```python
ids = db.create_many(
    table='users',
    data_list=[
        {'name': 'Иван', 'email': 'ivan@example.com'},
        {'name': 'Петр', 'email': 'petr@example.com'}
    ],
    returning='id'
)
```

### READ методы

#### `read(table, columns=None, where=None, order_by=None, limit=None, offset=None, as_dict=True)`
Читает записи из таблицы.

**Параметры:**
- `table` (str): Имя таблицы
- `columns` (list, optional): Список колонок для выборки
- `where` (dict, optional): Условия WHERE (поддерживает списки для IN)
- `order_by` (str, optional): Колонка для сортировки
- `limit` (int, optional): Максимальное количество записей
- `offset` (int, optional): Смещение для пагинации
- `as_dict` (bool): Возвращать результаты как словари (True) или кортежи (False)

**Возвращает:** Список словарей (если `as_dict=True`) или список кортежей (если `as_dict=False`)

**Пример:**
```python
users = db.read(
    table='users',
    where={'age': 30},
    order_by='name',
    limit=10
)
```

#### `read_one(table, columns=None, where=None, as_dict=True)`
Читает одну запись из таблицы.

**Параметры:**
- `table` (str): Имя таблицы
- `columns` (list, optional): Список колонок для выборки
- `where` (dict, optional): Условия WHERE
- `as_dict` (bool): Возвращать результат как словарь (True) или кортеж (False)

**Возвращает:** Одна запись (словарь или кортеж) или None

**Пример:**
```python
user = db.read_one(
    table='users',
    where={'email': 'ivan@example.com'}
)
```

#### `read_by_id(table, id_value, id_column='id', as_dict=True)`
Читает запись по ID.

**Параметры:**
- `table` (str): Имя таблицы
- `id_value` (Any): Значение ID
- `id_column` (str): Имя колонки с ID (по умолчанию 'id')
- `as_dict` (bool): Возвращать результат как словарь (True) или кортеж (False)

**Возвращает:** Запись (словарь или кортеж) или None

**Пример:**
```python
user = db.read_by_id(table='users', id_value=1)
```

### UPDATE методы

#### `update(table, data, where, returning=None)`
Обновляет записи в таблице.

**Параметры:**
- `table` (str): Имя таблицы
- `data` (dict): Данные для обновления
- `where` (dict): Условия WHERE (обязательно)
- `returning` (str, optional): Колонка для возврата после обновления

**Возвращает:** 
- Значение возвращаемой колонки (если `returning` указан)
- Количество обновленных строк (int, если `returning` не указан)

**Пример:**
```python
db.update(
    table='users',
    data={'age': 31},
    where={'id': 1}
)
```

#### `update_by_id(table, id_value, data, id_column='id', returning=None)`
Обновляет запись по ID.

**Параметры:**
- `table` (str): Имя таблицы
- `id_value` (Any): Значение ID
- `data` (dict): Данные для обновления
- `id_column` (str): Имя колонки с ID (по умолчанию 'id')
- `returning` (str, optional): Колонка для возврата после обновления

**Возвращает:** 
- Значение возвращаемой колонки (если `returning` указан)
- Количество обновленных строк (int, если `returning` не указан)

**Пример:**
```python
db.update_by_id(
    table='users',
    id_value=1,
    data={'age': 31}
)
```

### DELETE методы

#### `delete(table, where, returning=None)`
Удаляет записи из таблицы.

**Параметры:**
- `table` (str): Имя таблицы
- `where` (dict): Условия WHERE (обязательно)
- `returning` (str, optional): Колонка для возврата после удаления

**Возвращает:** 
- Значение возвращаемой колонки (если `returning` указан)
- Количество удаленных строк (int, если `returning` не указан)

**Пример:**
```python
db.delete(
    table='users',
    where={'age': 30}
)
```

#### `delete_by_id(table, id_value, id_column='id', returning=None)`
Удаляет запись по ID.

**Параметры:**
- `table` (str): Имя таблицы
- `id_value` (Any): Значение ID
- `id_column` (str): Имя колонки с ID (по умолчанию 'id')
- `returning` (str, optional): Колонка для возврата после удаления

**Возвращает:** 
- Значение возвращаемой колонки (если `returning` указан)
- Количество удаленных строк (int, если `returning` не указан)

**Пример:**
```python
db.delete_by_id(table='users', id_value=1)
```

### Утилиты

#### `count(table, where=None)`
Подсчитывает количество записей.

**Параметры:**
- `table` (str): Имя таблицы
- `where` (dict, optional): Условия WHERE

**Возвращает:** Количество записей (int)

**Пример:**
```python
total = db.count(table='users')
active = db.count(table='users', where={'active': True})
```

#### `exists(table, where)`
Проверяет существование записи.

**Параметры:**
- `table` (str): Имя таблицы
- `where` (dict): Условия WHERE

**Возвращает:** True если запись существует, False в противном случае

**Пример:**
```python
if db.exists(table='users', where={'email': 'ivan@example.com'}):
    print("Пользователь существует")
```

#### `execute_query(query, params=None, fetch=True, as_dict=False)`
Выполняет произвольный SQL запрос.

**Параметры:**
- `query` (str): SQL запрос
- `params` (tuple, optional): Параметры для запроса (кортеж)
- `fetch` (bool): Получать результаты запроса
- `as_dict` (bool): Возвращать результаты в виде словарей

**Возвращает:** Список результатов (словари или кортежи) или None (если `fetch=False`)

**Пример:**
```python
results = db.execute_query(
    query="SELECT * FROM users WHERE age > %s",
    params=(25,),
    as_dict=True
)
```

#### `execute_many(query, params_list)`
Выполняет запрос с множеством параметров.

**Параметры:**
- `query` (str): SQL запрос с плейсхолдерами
- `params_list` (list): Список кортежей с параметрами

**Возвращает:** None

**Пример:**
```python
db.execute_many(
    query="UPDATE users SET age = %s WHERE id = %s",
    params_list=[(31, 1), (32, 2)]
)
```

## Примеры использования

Смотрите файл `example_usage.py` для подробных примеров использования всех методов.

## Особенности

- ✅ Простой и интуитивный API
- ✅ Поддержка контекстного менеджера
- ✅ Автоматическое управление транзакциями (rollback при ошибках)
- ✅ Поддержка пула соединений
- ✅ Безопасность (защита от SQL-инъекций через параметризованные запросы)
- ✅ Гибкие условия WHERE (поддержка списков для оператора IN)
- ✅ Поддержка пагинации (limit/offset)
- ✅ Возврат результатов в виде словарей или кортежей
- ✅ Автоматическое переподключение при потере соединения

## Исключения

Драйвер может вызывать следующие исключения:

- `ConnectionError`: При ошибках подключения к базе данных
- `ValueError`: При пустых данных для вставки/обновления или отсутствии условий WHERE для UPDATE/DELETE
- `DatabaseError`: При ошибках выполнения SQL запросов

## Лицензия

MIT
