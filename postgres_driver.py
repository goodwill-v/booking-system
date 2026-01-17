"""
Модуль-драйвер для работы с PostgreSQL
Предоставляет удобный интерфейс для выполнения CRUD операций
"""
import os
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
from dotenv import load_dotenv
import psycopg2
from psycopg2 import OperationalError, DatabaseError, Error
from psycopg2.extras import RealDictCursor, execute_values
from psycopg2.pool import ThreadedConnectionPool


class PostgreSQLDriver:
    """
    Драйвер для работы с PostgreSQL базой данных.
    Предоставляет методы для выполнения CRUD операций.
    """
    
    def __init__(self, 
                 host: Optional[str] = None,
                 port: Optional[str] = None,
                 database: Optional[str] = None,
                 user: Optional[str] = None,
                 password: Optional[str] = None,
                 use_pool: bool = False,
                 pool_minconn: int = 1,
                 pool_maxconn: int = 10):
        """
        Инициализация драйвера PostgreSQL.
        
        Args:
            host: Хост базы данных (по умолчанию из DB_HOST)
            port: Порт базы данных (по умолчанию из DB_PORT)
            database: Имя базы данных (по умолчанию из DB_NAME)
            user: Пользователь (по умолчанию из DB_USER)
            password: Пароль (по умолчанию из DB_PASSWORD)
            use_pool: Использовать пул соединений
            pool_minconn: Минимальное количество соединений в пуле
            pool_maxconn: Максимальное количество соединений в пуле
        """
        # Загружаем переменные окружения
        load_dotenv()
        
        # Получаем параметры подключения
        self.host = host or os.getenv('DB_HOST', 'localhost')
        self.port = port or os.getenv('DB_PORT', '5432')
        self.database = database or os.getenv('DB_NAME', 'postgres')
        self.user = user or os.getenv('DB_USER', 'postgres')
        self.password = password or os.getenv('DB_PASSWORD', '')
        
        self.use_pool = use_pool
        self.connection_pool: Optional[ThreadedConnectionPool] = None
        self.connection = None
        
        if use_pool:
            self._create_pool(pool_minconn, pool_maxconn)
    
    def _get_connection_params(self) -> Dict[str, Any]:
        """Получает параметры подключения"""
        return {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.user,
            'password': self.password
        }
    
    def _create_pool(self, minconn: int, maxconn: int):
        """Создает пул соединений"""
        try:
            self.connection_pool = ThreadedConnectionPool(
                minconn=minconn,
                maxconn=maxconn,
                **self._get_connection_params()
            )
        except Exception as e:
            raise ConnectionError(f"Не удалось создать пул соединений: {e}")
    
    def connect(self) -> bool:
        """
        Устанавливает соединение с базой данных.
        
        Returns:
            True если подключение успешно, False в противном случае
        """
        try:
            if self.use_pool and self.connection_pool:
                self.connection = self.connection_pool.getconn()
            else:
                self.connection = psycopg2.connect(**self._get_connection_params())
            return True
        except OperationalError as e:
            raise ConnectionError(f"Ошибка подключения к базе данных: {e}")
        except Exception as e:
            raise ConnectionError(f"Неожиданная ошибка при подключении: {e}")
    
    def disconnect(self):
        """Закрывает соединение с базой данных"""
        if self.connection:
            if self.use_pool and self.connection_pool:
                self.connection_pool.putconn(self.connection)
            else:
                self.connection.close()
            self.connection = None
    
    def _ensure_connection(self):
        """Проверяет наличие активного соединения"""
        if not self.connection or self.connection.closed:
            self.connect()
    
    @contextmanager
    def get_cursor(self, dict_cursor: bool = False):
        """
        Контекстный менеджер для работы с курсором.
        
        Args:
            dict_cursor: Если True, возвращает курсор с результатами в виде словарей
        
        Yields:
            Курсор базы данных
        """
        self._ensure_connection()
        cursor_class = RealDictCursor if dict_cursor else None
        cursor = self.connection.cursor(cursor_factory=cursor_class)
        try:
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            cursor.close()
    
    # ==================== CREATE (INSERT) ====================
    
    def create(self, 
               table: str, 
               data: Dict[str, Any],
               returning: Optional[str] = None) -> Optional[Any]:
        """
        Вставляет новую запись в таблицу.
        
        Args:
            table: Имя таблицы
            data: Словарь с данными для вставки (ключ - имя колонки, значение - значение)
            returning: Колонка для возврата после вставки (например, 'id')
        
        Returns:
            Значение возвращаемой колонки или None
        """
        if not data:
            raise ValueError("Данные для вставки не могут быть пустыми")
        
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        values = list(data.values())
        
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        if returning:
            query += f" RETURNING {returning}"
        
        with self.get_cursor() as cursor:
            cursor.execute(query, values)
            if returning:
                result = cursor.fetchone()
                return result[0] if result else None
            return None
    
    def create_many(self, 
                    table: str, 
                    data_list: List[Dict[str, Any]],
                    returning: Optional[str] = None) -> List[Any]:
        """
        Вставляет несколько записей в таблицу.
        
        Args:
            table: Имя таблицы
            data_list: Список словарей с данными для вставки
            returning: Колонка для возврата после вставки
        
        Returns:
            Список значений возвращаемой колонки или пустой список
        """
        if not data_list:
            return []
        
        # Получаем колонки из первого элемента
        columns = ', '.join(data_list[0].keys())
        values = [tuple(item.values()) for item in data_list]
        
        query = f"INSERT INTO {table} ({columns}) VALUES %s"
        
        if returning:
            query += f" RETURNING {returning}"
        
        with self.get_cursor() as cursor:
            if returning:
                results = []
                for value_tuple in values:
                    cursor.execute(
                        f"INSERT INTO {table} ({columns}) VALUES ({', '.join(['%s'] * len(value_tuple))}) RETURNING {returning}",
                        value_tuple
                    )
                    result = cursor.fetchone()
                    if result:
                        results.append(result[0])
                return results
            else:
                execute_values(cursor, query, values)
                return []
    
    # ==================== READ (SELECT) ====================
    
    def read(self, 
             table: str,
             columns: Optional[List[str]] = None,
             where: Optional[Dict[str, Any]] = None,
             order_by: Optional[str] = None,
             limit: Optional[int] = None,
             offset: Optional[int] = None,
             as_dict: bool = True) -> List[Dict[str, Any]]:
        """
        Читает данные из таблицы.
        
        Args:
            table: Имя таблицы
            columns: Список колонок для выборки (по умолчанию все)
            where: Словарь условий WHERE (ключ - колонка, значение - значение для сравнения)
            order_by: Колонка для сортировки
            limit: Максимальное количество записей
            offset: Смещение для пагинации
            as_dict: Возвращать результаты в виде словарей
        
        Returns:
            Список записей
        """
        cols = ', '.join(columns) if columns else '*'
        query = f"SELECT {cols} FROM {table}"
        params = []
        
        # Добавляем условия WHERE
        if where:
            conditions = []
            for key, value in where.items():
                if isinstance(value, (list, tuple)):
                    placeholders = ', '.join(['%s'] * len(value))
                    conditions.append(f"{key} IN ({placeholders})")
                    params.extend(value)
                else:
                    conditions.append(f"{key} = %s")
                    params.append(value)
            query += " WHERE " + " AND ".join(conditions)
        
        # Добавляем сортировку
        if order_by:
            query += f" ORDER BY {order_by}"
        
        # Добавляем лимит
        if limit:
            query += f" LIMIT {limit}"
        
        # Добавляем смещение
        if offset:
            query += f" OFFSET {offset}"
        
        with self.get_cursor(dict_cursor=as_dict) as cursor:
            cursor.execute(query, params)
            if as_dict:
                return [dict(row) for row in cursor.fetchall()]
            else:
                return cursor.fetchall()
    
    def read_one(self, 
                 table: str,
                 columns: Optional[List[str]] = None,
                 where: Optional[Dict[str, Any]] = None,
                 as_dict: bool = True) -> Optional[Dict[str, Any]]:
        """
        Читает одну запись из таблицы.
        
        Args:
            table: Имя таблицы
            columns: Список колонок для выборки
            where: Словарь условий WHERE
            as_dict: Возвращать результат в виде словаря
        
        Returns:
            Одна запись или None
        """
        results = self.read(table, columns, where, limit=1, as_dict=as_dict)
        return results[0] if results else None
    
    def read_by_id(self, 
                   table: str,
                   id_value: Any,
                   id_column: str = 'id',
                   as_dict: bool = True) -> Optional[Dict[str, Any]]:
        """
        Читает запись по ID.
        
        Args:
            table: Имя таблицы
            id_value: Значение ID
            id_column: Имя колонки с ID (по умолчанию 'id')
            as_dict: Возвращать результат в виде словаря
        
        Returns:
            Запись или None
        """
        return self.read_one(table, where={id_column: id_value}, as_dict=as_dict)
    
    # ==================== UPDATE ====================
    
    def update(self, 
               table: str,
               data: Dict[str, Any],
               where: Dict[str, Any],
               returning: Optional[str] = None) -> Optional[Any]:
        """
        Обновляет записи в таблице.
        
        Args:
            table: Имя таблицы
            data: Словарь с данными для обновления
            where: Словарь условий WHERE
            returning: Колонка для возврата после обновления
        
        Returns:
            Значение возвращаемой колонки или None
        """
        if not data:
            raise ValueError("Данные для обновления не могут быть пустыми")
        if not where:
            raise ValueError("Условие WHERE обязательно для операции UPDATE")
        
        set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
        where_clause = ' AND '.join([f"{key} = %s" for key in where.keys()])
        
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        params = list(data.values()) + list(where.values())
        
        if returning:
            query += f" RETURNING {returning}"
        
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            if returning:
                result = cursor.fetchone()
                return result[0] if result else None
            return cursor.rowcount
    
    def update_by_id(self, 
                     table: str,
                     id_value: Any,
                     data: Dict[str, Any],
                     id_column: str = 'id',
                     returning: Optional[str] = None) -> Optional[Any]:
        """
        Обновляет запись по ID.
        
        Args:
            table: Имя таблицы
            id_value: Значение ID
            data: Словарь с данными для обновления
            id_column: Имя колонки с ID
            returning: Колонка для возврата после обновления
        
        Returns:
            Значение возвращаемой колонки или количество обновленных строк
        """
        return self.update(table, data, {id_column: id_value}, returning)
    
    # ==================== DELETE ====================
    
    def delete(self, 
               table: str,
               where: Dict[str, Any],
               returning: Optional[str] = None) -> Optional[Any]:
        """
        Удаляет записи из таблицы.
        
        Args:
            table: Имя таблицы
            where: Словарь условий WHERE
            returning: Колонка для возврата после удаления
        
        Returns:
            Значение возвращаемой колонки или количество удаленных строк
        """
        if not where:
            raise ValueError("Условие WHERE обязательно для операции DELETE")
        
        where_clause = ' AND '.join([f"{key} = %s" for key in where.keys()])
        query = f"DELETE FROM {table} WHERE {where_clause}"
        params = list(where.values())
        
        if returning:
            query += f" RETURNING {returning}"
        
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            if returning:
                result = cursor.fetchone()
                return result[0] if result else None
            return cursor.rowcount
    
    def delete_by_id(self, 
                     table: str,
                     id_value: Any,
                     id_column: str = 'id',
                     returning: Optional[str] = None) -> Optional[Any]:
        """
        Удаляет запись по ID.
        
        Args:
            table: Имя таблицы
            id_value: Значение ID
            id_column: Имя колонки с ID
            returning: Колонка для возврата после удаления
        
        Returns:
            Значение возвращаемой колонки или количество удаленных строк
        """
        return self.delete(table, {id_column: id_value}, returning)
    
    # ==================== UTILITY METHODS ====================
    
    def execute_query(self, 
                     query: str,
                     params: Optional[Tuple] = None,
                     fetch: bool = True,
                     as_dict: bool = False) -> Optional[List[Any]]:
        """
        Выполняет произвольный SQL запрос.
        
        Args:
            query: SQL запрос
            params: Параметры для запроса
            fetch: Получать результаты запроса
            as_dict: Возвращать результаты в виде словарей
        
        Returns:
            Результаты запроса или None
        """
        with self.get_cursor(dict_cursor=as_dict) as cursor:
            cursor.execute(query, params)
            if fetch:
                if as_dict:
                    return [dict(row) for row in cursor.fetchall()]
                return cursor.fetchall()
            return None
    
    def execute_many(self, query: str, params_list: List[Tuple]):
        """
        Выполняет запрос с множеством параметров.
        
        Args:
            query: SQL запрос с плейсхолдерами
            params_list: Список кортежей с параметрами
        """
        with self.get_cursor() as cursor:
            cursor.executemany(query, params_list)
    
    def count(self, table: str, where: Optional[Dict[str, Any]] = None) -> int:
        """
        Подсчитывает количество записей в таблице.
        
        Args:
            table: Имя таблицы
            where: Словарь условий WHERE
        
        Returns:
            Количество записей
        """
        query = f"SELECT COUNT(*) FROM {table}"
        params = []
        
        if where:
            conditions = []
            for key, value in where.items():
                conditions.append(f"{key} = %s")
                params.append(value)
            query += " WHERE " + " AND ".join(conditions)
        
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result[0] if result else 0
    
    def exists(self, table: str, where: Dict[str, Any]) -> bool:
        """
        Проверяет существование записи.
        
        Args:
            table: Имя таблицы
            where: Словарь условий WHERE
        
        Returns:
            True если запись существует, False в противном случае
        """
        return self.count(table, where) > 0
    
    def create_table_from_model(self, model_class: type) -> bool:
        """
        Создает таблицу на основе модели, если она не существует.
        
        Метод использует SQL из метода get_create_table_sql() модели для создания
        таблицы и всех связанных индексов.
        
        Args:
            model_class: Класс модели (например, User, RestaurantTable, Booking),
                        который должен иметь метод get_create_table_sql()
        
        Returns:
            True если таблица успешно создана или уже существует, False в случае ошибки
        
        Raises:
            AttributeError: Если модель не имеет метода get_create_table_sql()
            DatabaseError: Если произошла ошибка при выполнении SQL
        """
        if not hasattr(model_class, 'get_create_table_sql'):
            raise AttributeError(
                f"Модель {model_class.__name__} должна иметь метод get_create_table_sql()"
            )
        
        try:
            # Получаем SQL из модели
            sql = model_class.get_create_table_sql()
            
            # Разбиваем SQL на отдельные команды (разделитель - точка с запятой)
            # Убираем пустые строки и пробелы
            commands = [cmd.strip() for cmd in sql.split(';') if cmd.strip()]
            
            # Выполняем каждую команду отдельно
            with self.get_cursor() as cursor:
                for command in commands:
                    if command:  # Проверяем, что команда не пустая
                        cursor.execute(command)
            
            return True
        except DatabaseError as e:
            raise DatabaseError(f"Ошибка при создании таблицы из модели {model_class.__name__}: {e}")
        except Exception as e:
            raise Exception(f"Неожиданная ошибка при создании таблицы: {e}")
    
    def __enter__(self):
        """Поддержка контекстного менеджера"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Поддержка контекстного менеджера"""
        self.disconnect()
    
    def __del__(self):
        """Закрывает соединение при удалении объекта"""
        if hasattr(self, 'connection') and self.connection:
            self.disconnect()
        if hasattr(self, 'connection_pool') and self.connection_pool:
            self.connection_pool.closeall()
