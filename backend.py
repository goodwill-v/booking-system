"""
Backend модуль для инициализации базы данных
Создает все необходимые таблицы на основе моделей
Предоставляет CRUD операции для всех моделей
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from postgres_driver import PostgreSQLDriver
from models.users import User
from models.tables import RestaurantTable
from models.booking import Booking


def create_all_tables(driver: PostgreSQLDriver = None) -> bool:
    """
    Создает все таблицы для всех моделей из папки models.
    
    Таблицы создаются в правильном порядке:
    1. users - независимая таблица
    2. restaurant_tables - независимая таблица
    3. bookings - зависит от users и restaurant_tables (внешние ключи)
    
    Args:
        driver: Экземпляр PostgreSQLDriver. Если не передан, создается новый.
    
    Returns:
        True если все таблицы успешно созданы, False в случае ошибки
    """
    # Список всех моделей в порядке создания (сначала независимые, потом зависимые)
    models = [
        User,              # Независимая таблица
        RestaurantTable,   # Независимая таблица
        Booking           # Зависит от User и RestaurantTable
    ]
    
    # Создаем драйвер, если не передан
    if driver is None:
        driver = PostgreSQLDriver()
    
    try:
        # Подключаемся к базе данных
        driver.connect()
        
        print("Начинаем создание таблиц...")
        
        # Создаем таблицы для каждой модели
        for model in models:
            model_name = model.__name__
            table_name = model.get_table_name()
            
            print(f"Создание таблицы '{table_name}' для модели {model_name}...")
            
            try:
                driver.create_table_from_model(model)
                print(f"✓ Таблица '{table_name}' успешно создана")
            except Exception as e:
                print(f"✗ Ошибка при создании таблицы '{table_name}': {e}")
                raise
        
        print("\nВсе таблицы успешно созданы!")
        return True
        
    except Exception as e:
        print(f"\nОшибка при создании таблиц: {e}")
        return False
        
    finally:
        # Закрываем соединение
        driver.disconnect()


# ==================== CRUD ОПЕРАЦИИ ДЛЯ USERS ====================

def create_user(user: User, driver: PostgreSQLDriver) -> Optional[int]:
    """
    Создает нового пользователя в базе данных.
    
    Args:
        user: Объект User для создания
        driver: Экземпляр PostgreSQLDriver
    
    Returns:
        ID созданного пользователя или None в случае ошибки
    """
    try:
        user_data = user.to_dict()
        user_id = driver.create(User.get_table_name(), user_data, returning='id')
        return user_id
    except Exception as e:
        print(f"Ошибка при создании пользователя: {e}")
        return None


def read_user(user_id: int, driver: PostgreSQLDriver) -> Optional[User]:
    """
    Читает пользователя по ID.
    
    Args:
        user_id: ID пользователя
        driver: Экземпляр PostgreSQLDriver
    
    Returns:
        Объект User или None если не найден
    """
    try:
        data = driver.read_by_id(User.get_table_name(), user_id, as_dict=True)
        if data:
            return User.from_dict(data)
        return None
    except Exception as e:
        print(f"Ошибка при чтении пользователя: {e}")
        return None


def read_users(where: Optional[Dict[str, Any]] = None, 
               driver: PostgreSQLDriver = None) -> List[User]:
    """
    Читает список пользователей с опциональными условиями.
    
    Args:
        where: Словарь условий для фильтрации (например, {'role': 'admin'})
        driver: Экземпляр PostgreSQLDriver
    
    Returns:
        Список объектов User
    """
    if driver is None:
        driver = PostgreSQLDriver()
        driver.connect()
        should_disconnect = True
    else:
        should_disconnect = False
    
    try:
        data_list = driver.read(User.get_table_name(), where=where, as_dict=True)
        users = [User.from_dict(data) for data in data_list]
        return users
    except Exception as e:
        print(f"Ошибка при чтении пользователей: {e}")
        return []
    finally:
        if should_disconnect:
            driver.disconnect()


def update_user(user_id: int, user: User, driver: PostgreSQLDriver) -> bool:
    """
    Обновляет данные пользователя.
    
    Args:
        user_id: ID пользователя для обновления
        user: Объект User с новыми данными
        driver: Экземпляр PostgreSQLDriver
    
    Returns:
        True если обновление успешно, False в противном случае
    """
    try:
        user_data = user.to_dict()
        # Обновляем updated_at
        from datetime import datetime
        user_data['updated_at'] = datetime.now()
        
        rows_affected = driver.update_by_id(
            User.get_table_name(), 
            user_id, 
            user_data
        )
        return rows_affected > 0
    except Exception as e:
        print(f"Ошибка при обновлении пользователя: {e}")
        return False


def delete_user(user_id: int, driver: PostgreSQLDriver) -> bool:
    """
    Удаляет пользователя по ID.
    
    Args:
        user_id: ID пользователя для удаления
        driver: Экземпляр PostgreSQLDriver
    
    Returns:
        True если удаление успешно, False в противном случае
    """
    try:
        rows_affected = driver.delete_by_id(User.get_table_name(), user_id)
        return rows_affected > 0
    except Exception as e:
        print(f"Ошибка при удалении пользователя: {e}")
        return False


# ==================== CRUD ОПЕРАЦИИ ДЛЯ RESTAURANT_TABLES ====================

def create_table(table: RestaurantTable, driver: PostgreSQLDriver) -> Optional[int]:
    """
    Создает новый стол в базе данных.
    
    Args:
        table: Объект RestaurantTable для создания
        driver: Экземпляр PostgreSQLDriver
    
    Returns:
        ID созданного стола или None в случае ошибки
    """
    try:
        table_data = table.to_dict()
        table_id = driver.create(RestaurantTable.get_table_name(), table_data, returning='id')
        return table_id
    except Exception as e:
        print(f"Ошибка при создании стола: {e}")
        return None


def read_table(table_id: int, driver: PostgreSQLDriver) -> Optional[RestaurantTable]:
    """
    Читает стол по ID.
    
    Args:
        table_id: ID стола
        driver: Экземпляр PostgreSQLDriver
    
    Returns:
        Объект RestaurantTable или None если не найден
    """
    try:
        data = driver.read_by_id(RestaurantTable.get_table_name(), table_id, as_dict=True)
        if data:
            return RestaurantTable.from_dict(data)
        return None
    except Exception as e:
        print(f"Ошибка при чтении стола: {e}")
        return None


def read_tables(where: Optional[Dict[str, Any]] = None,
                driver: PostgreSQLDriver = None) -> List[RestaurantTable]:
    """
    Читает список столов с опциональными условиями.
    
    Args:
        where: Словарь условий для фильтрации (например, {'status': 'available'})
        driver: Экземпляр PostgreSQLDriver
    
    Returns:
        Список объектов RestaurantTable
    """
    if driver is None:
        driver = PostgreSQLDriver()
        driver.connect()
        should_disconnect = True
    else:
        should_disconnect = False
    
    try:
        data_list = driver.read(RestaurantTable.get_table_name(), where=where, as_dict=True)
        tables = [RestaurantTable.from_dict(data) for data in data_list]
        return tables
    except Exception as e:
        print(f"Ошибка при чтении столов: {e}")
        return []
    finally:
        if should_disconnect:
            driver.disconnect()


def update_table(table_id: int, table: RestaurantTable, driver: PostgreSQLDriver) -> bool:
    """
    Обновляет данные стола.
    
    Args:
        table_id: ID стола для обновления
        table: Объект RestaurantTable с новыми данными
        driver: Экземпляр PostgreSQLDriver
    
    Returns:
        True если обновление успешно, False в противном случае
    """
    try:
        table_data = table.to_dict()
        # Обновляем updated_at
        from datetime import datetime
        table_data['updated_at'] = datetime.now()
        
        rows_affected = driver.update_by_id(
            RestaurantTable.get_table_name(),
            table_id,
            table_data
        )
        return rows_affected > 0
    except Exception as e:
        print(f"Ошибка при обновлении стола: {e}")
        return False


def delete_table(table_id: int, driver: PostgreSQLDriver) -> bool:
    """
    Удаляет стол по ID.
    
    Args:
        table_id: ID стола для удаления
        driver: Экземпляр PostgreSQLDriver
    
    Returns:
        True если удаление успешно, False в противном случае
    """
    try:
        rows_affected = driver.delete_by_id(RestaurantTable.get_table_name(), table_id)
        return rows_affected > 0
    except Exception as e:
        print(f"Ошибка при удалении стола: {e}")
        return False


# ==================== CRUD ОПЕРАЦИИ ДЛЯ BOOKINGS ====================

def create_booking(booking: Booking, driver: PostgreSQLDriver) -> Optional[int]:
    """
    Создает новое бронирование в базе данных.
    Перед созданием проверяет доступность стола на указанное время.
    
    Args:
        booking: Объект Booking для создания
        driver: Экземпляр PostgreSQLDriver
    
    Returns:
        ID созданного бронирования или None в случае ошибки
    """
    try:
        # Проверяем, что booking_end_time задано
        if not booking.booking_end_time:
            print("Ошибка: booking_end_time должно быть задано")
            return None
        
        # Получаем дату и время для проверки доступности
        from datetime import date, time, datetime
        
        booking_date = booking.booking_date
        if isinstance(booking_date, datetime):
            booking_date = booking_date.date()
        
        booking_time_start = booking.booking_time
        if isinstance(booking_time_start, datetime):
            booking_time_start = booking_time_start.time()
        
        booking_time_end = booking.booking_end_time
        if isinstance(booking_time_end, datetime):
            booking_time_end = booking_time_end.time()
        
        # Проверяем доступность стола
        availability_result = check_table_availability(
            table_id=booking.table_id,
            booking_date=booking_date,
            booking_time=booking_time_start,
            booking_end_time=booking_time_end,
            driver=driver
        )
        
        if not availability_result['available']:
            if not availability_result['table_exists']:
                print("Ошибка: Стол с указанным ID не существует")
            elif not availability_result['table_active']:
                print("Ошибка: Стол неактивен")
            else:
                conflict = availability_result.get('conflicting_booking')
                if conflict:
                    print(f"Ошибка: Стол уже забронирован на это время (конфликт с бронированием ID: {conflict.id})")
                else:
                    print("Ошибка: Стол недоступен на указанное время")
            return None
        
        # Если стол доступен, создаем бронирование
        booking_data = booking.to_dict()
        booking_id = driver.create(Booking.get_table_name(), booking_data, returning='id')
        return booking_id
    except Exception as e:
        print(f"Ошибка при создании бронирования: {e}")
        return None


def read_booking(booking_id: int, driver: PostgreSQLDriver) -> Optional[Booking]:
    """
    Читает бронирование по ID.
    
    Args:
        booking_id: ID бронирования
        driver: Экземпляр PostgreSQLDriver
    
    Returns:
        Объект Booking или None если не найден
    """
    try:
        data = driver.read_by_id(Booking.get_table_name(), booking_id, as_dict=True)
        if data:
            return Booking.from_dict(data)
        return None
    except Exception as e:
        print(f"Ошибка при чтении бронирования: {e}")
        return None


def read_bookings(where: Optional[Dict[str, Any]] = None,
                  driver: PostgreSQLDriver = None) -> List[Booking]:
    """
    Читает список бронирований с опциональными условиями.
    
    Args:
        where: Словарь условий для фильтрации (например, {'user_id': 1, 'status': 'confirmed'})
        driver: Экземпляр PostgreSQLDriver
    
    Returns:
        Список объектов Booking
    """
    if driver is None:
        driver = PostgreSQLDriver()
        driver.connect()
        should_disconnect = True
    else:
        should_disconnect = False
    
    try:
        data_list = driver.read(Booking.get_table_name(), where=where, as_dict=True)
        bookings = [Booking.from_dict(data) for data in data_list]
        return bookings
    except Exception as e:
        print(f"Ошибка при чтении бронирований: {e}")
        return []
    finally:
        if should_disconnect:
            driver.disconnect()


def update_booking(booking_id: int, booking: Booking, driver: PostgreSQLDriver) -> bool:
    """
    Обновляет данные бронирования.
    
    Args:
        booking_id: ID бронирования для обновления
        booking: Объект Booking с новыми данными
        driver: Экземпляр PostgreSQLDriver
    
    Returns:
        True если обновление успешно, False в противном случае
    """
    try:
        booking_data = booking.to_dict()
        # Обновляем updated_at
        from datetime import datetime
        booking_data['updated_at'] = datetime.now()
        
        rows_affected = driver.update_by_id(
            Booking.get_table_name(),
            booking_id,
            booking_data
        )
        return rows_affected > 0
    except Exception as e:
        print(f"Ошибка при обновлении бронирования: {e}")
        return False


def delete_booking(booking_id: int, driver: PostgreSQLDriver) -> bool:
    """
    Удаляет бронирование по ID.
    
    Args:
        booking_id: ID бронирования для удаления
        driver: Экземпляр PostgreSQLDriver
    
    Returns:
        True если удаление успешно, False в противном случае
    """
    try:
        rows_affected = driver.delete_by_id(Booking.get_table_name(), booking_id)
        return rows_affected > 0
    except Exception as e:
        print(f"Ошибка при удалении бронирования: {e}")
        return False


def check_table_availability(table_id: int, 
                              booking_date: date,
                              booking_time: time,
                              booking_end_time: time,
                              driver: PostgreSQLDriver,
                              exclude_booking_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Проверяет, свободен ли стол на выбранное время с учетом пересекающихся бронирований.
    
    Функция проверяет не только точное совпадение времени, но и пересечения временных интервалов.
    Например, если есть бронирование с 19:00 до 21:00, то нельзя забронировать стол
    на 20:00 или на 18:30-20:30, так как времена пересекаются.
    
    Args:
        table_id: ID стола для проверки
        booking_date: Дата бронирования
        booking_time: Время начала бронирования
        booking_end_time: Время окончания бронирования
        driver: Экземпляр PostgreSQLDriver
        exclude_booking_id: ID бронирования для исключения из проверки 
                           (полезно при обновлении существующего бронирования)
    
    Returns:
        Словарь с результатами проверки:
        {
            'available': bool - свободен ли стол,
            'table_exists': bool - существует ли стол,
            'table_active': bool - активен ли стол,
            'conflicting_booking': Optional[Booking] - конфликтующее бронирование если есть
        }
    """
    result = {
        'available': False,
        'table_exists': False,
        'table_active': False,
        'conflicting_booking': None
    }
    
    try:
        # Проверяем, существует ли стол
        table = read_table(table_id, driver)
        if not table:
            return result  # Стол не существует
        
        result['table_exists'] = True
        
        # Проверяем, активен ли стол
        if not table.is_active:
            return result  # Стол неактивен
        
        result['table_active'] = True
        
        # Получаем все активные бронирования на эту дату для этого стола
        where_conditions = {
            'table_id': table_id,
            'booking_date': booking_date
        }
        
        # Получаем все бронирования на эту дату
        bookings = read_bookings(where=where_conditions, driver=driver)
        
        # Фильтруем активные бронирования (исключаем отмененные и завершенные)
        active_bookings = [
            b for b in bookings 
            if b.status in ['pending', 'confirmed'] 
            and (exclude_booking_id is None or b.id != exclude_booking_id)
        ]
        
        # Вычисляем время начала и окончания нового бронирования
        from datetime import datetime
        
        # Преобразуем booking_time и booking_end_time в datetime для удобных вычислений
        new_start = datetime.combine(booking_date, booking_time)
        new_end = datetime.combine(booking_date, booking_end_time)
        
        # Проверяем пересечения с существующими бронированиями
        for existing_booking in active_bookings:
            # Получаем время начала существующего бронирования
            existing_time_start = existing_booking.booking_time
            if isinstance(existing_time_start, datetime):
                existing_time_start = existing_time_start.time()
            
            # Получаем время окончания существующего бронирования
            if existing_booking.booking_end_time:
                existing_time_end = existing_booking.booking_end_time
                if isinstance(existing_time_end, datetime):
                    existing_time_end = existing_time_end.time()
            else:
                # Если booking_end_time не задано, вычисляем его как время начала + 2 часа (для обратной совместимости)
                from datetime import timedelta
                existing_start_dt = datetime.combine(booking_date, existing_time_start)
                existing_time_end = (existing_start_dt + timedelta(hours=2.0)).time()
            
            # Вычисляем время начала и окончания существующего бронирования
            existing_start = datetime.combine(booking_date, existing_time_start)
            existing_end = datetime.combine(booking_date, existing_time_end)
            
            # Проверяем пересечение временных интервалов
            # Интервалы пересекаются, если НЕ выполняется условие:
            # новое_окончание <= существующее_начало ИЛИ новое_начало >= существующее_окончание
            # Примечание: если новое бронирование начинается точно в момент окончания существующего
            # (или наоборот), это НЕ считается пересечением - столы могут быть забронированы последовательно
            if not (new_end <= existing_start or new_start >= existing_end):
                # Найдено пересечение - временные интервалы перекрываются
                result['conflicting_booking'] = existing_booking
                return result
        
        # Стол свободен, пересечений не найдено
        result['available'] = True
        return result
        
    except Exception as e:
        print(f"Ошибка при проверке доступности стола: {e}")
        return result


# ==================== ФУНКЦИИ ПОЛУЧЕНИЯ ВСЕХ ОБЪЕКТОВ ====================

def get_all_users(driver: PostgreSQLDriver = None) -> List[User]:
    """
    Получает всех пользователей из базы данных.
    
    Args:
        driver: Экземпляр PostgreSQLDriver. Если не передан, создается новый.
    
    Returns:
        Список всех объектов User
    """
    return read_users(where=None, driver=driver)


def get_all_tables(driver: PostgreSQLDriver = None) -> List[RestaurantTable]:
    """
    Получает все столы из базы данных.
    
    Args:
        driver: Экземпляр PostgreSQLDriver. Если не передан, создается новый.
    
    Returns:
        Список всех объектов RestaurantTable
    """
    return read_tables(where=None, driver=driver)


def get_all_bookings(driver: PostgreSQLDriver = None) -> List[Booking]:
    """
    Получает все бронирования из базы данных.
    
    Args:
        driver: Экземпляр PostgreSQLDriver. Если не передан, создается новый.
    
    Returns:
        Список всех объектов Booking
    """
    return read_bookings(where=None, driver=driver)


if __name__ == "__main__":
    """
    Если файл запускается напрямую, создаем все таблицы
    """
    print("=" * 50)
    print("Инициализация базы данных")
    print("=" * 50)
    
    success = create_all_tables()
    
    if success:
        print("\n✓ Инициализация завершена успешно")
    else:
        print("\n✗ Инициализация завершена с ошибками")
