"""
Модель бронирования для системы бронирования ресторана
Содержит базовые поля, необходимые для работы с таблицей bookings
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Booking:
    """
    Модель бронирования стола в ресторане.
    
    Поля:
        id: Уникальный идентификатор бронирования (первичный ключ)
        user_id: Внешний ключ на таблицу users (ID пользователя, который делает бронирование)
        table_id: Внешний ключ на таблицу restaurant_tables (ID стола, который бронируется)
        booking_date: Дата бронирования
        booking_time: Время начала бронирования
        booking_end_time: Время окончания бронирования
        number_of_guests: Количество гостей
        status: Статус бронирования ('pending', 'confirmed', 'cancelled', 'completed')
        notes: Дополнительные заметки к бронированию (опционально)
        created_at: Дата и время создания записи
        updated_at: Дата и время последнего обновления записи
    """
    id: Optional[int] = None
    user_id: int = 0  # Внешний ключ на users.id
    table_id: int = 0  # Внешний ключ на restaurant_tables.id
    booking_date: Optional[datetime] = None
    booking_time: Optional[datetime] = None  # Время начала бронирования
    booking_end_time: Optional[datetime] = None  # Время окончания бронирования
    number_of_guests: int = 1
    status: str = "pending"  # По умолчанию ожидает подтверждения
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def get_table_name(cls) -> str:
        """Возвращает имя таблицы в базе данных"""
        return "bookings"
    
    @classmethod
    def get_create_table_sql(cls) -> str:
        """
        Возвращает SQL запрос для создания таблицы bookings.
        Можно использовать для миграций или инициализации БД.
        """
        return """
        CREATE TABLE IF NOT EXISTS bookings (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            table_id INTEGER NOT NULL,
            booking_date DATE NOT NULL,
            booking_time TIME NOT NULL,
            booking_end_time TIME NOT NULL,
            number_of_guests INTEGER NOT NULL CHECK (number_of_guests > 0),
            status VARCHAR(50) DEFAULT 'pending' NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (table_id) REFERENCES restaurant_tables(id) ON DELETE RESTRICT,
            CHECK (booking_end_time > booking_time)
        );
        
        CREATE INDEX IF NOT EXISTS idx_bookings_user_id ON bookings(user_id);
        CREATE INDEX IF NOT EXISTS idx_bookings_table_id ON bookings(table_id);
        CREATE INDEX IF NOT EXISTS idx_bookings_date ON bookings(booking_date);
        CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);
        CREATE INDEX IF NOT EXISTS idx_bookings_date_time ON bookings(booking_date, booking_time);
        CREATE INDEX IF NOT EXISTS idx_bookings_date_time_end ON bookings(booking_date, booking_time, booking_end_time);
        """
    
    def to_dict(self) -> dict:
        """Преобразует объект бронирования в словарь для работы с БД"""
        result = {
            'user_id': self.user_id,
            'table_id': self.table_id,
            'booking_date': self.booking_date.date() if isinstance(self.booking_date, datetime) else self.booking_date,
            'booking_time': self.booking_time.time() if isinstance(self.booking_time, datetime) else self.booking_time,
            'number_of_guests': self.number_of_guests,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        # Добавляем booking_end_time (обязательное поле)
        if self.booking_end_time is not None:
            result['booking_end_time'] = self.booking_end_time.time() if isinstance(self.booking_end_time, datetime) else self.booking_end_time
        else:
            # Если booking_end_time не задано, это ошибка, но для обратной совместимости
            # можно вычислить его как booking_time + 2 часа
            from datetime import timedelta
            if self.booking_time:
                booking_time_obj = self.booking_time.time() if isinstance(self.booking_time, datetime) else self.booking_time
                booking_date_obj = self.booking_date.date() if isinstance(self.booking_date, datetime) else self.booking_date
                if booking_date_obj and booking_time_obj:
                    booking_dt = datetime.combine(booking_date_obj, booking_time_obj)
                    end_time = (booking_dt + timedelta(hours=2.0)).time()
                    result['booking_end_time'] = end_time
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Booking':
        """Создает объект бронирования из словаря (например, из результата БД)"""
        # Обработка booking_date и booking_time
        booking_date = data.get('booking_date')
        booking_time = data.get('booking_time')
        
        # Если это datetime объекты, оставляем как есть, иначе преобразуем
        if booking_date and not isinstance(booking_date, datetime):
            # Если это date объект, можно оставить как есть или преобразовать
            pass
        if booking_time and not isinstance(booking_time, datetime):
            # Если это time объект, можно оставить как есть или преобразовать
            pass
        
        # Обработка booking_end_time
        booking_end_time = data.get('booking_end_time')
        
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id', 0),
            table_id=data.get('table_id', 0),
            booking_date=booking_date,
            booking_time=booking_time,
            booking_end_time=booking_end_time,
            number_of_guests=data.get('number_of_guests', 1),
            status=data.get('status', 'pending'),
            notes=data.get('notes'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
