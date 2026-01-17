"""
Модель стола для системы бронирования ресторана
Содержит базовые поля, необходимые для работы с таблицей restaurant_tables
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class RestaurantTable:
    """
    Модель стола в ресторане для системы бронирования.
    
    Поля:
        id: Уникальный идентификатор стола (первичный ключ)
        table_number: Номер стола (уникальный, для идентификации)
        capacity: Вместимость стола (количество мест)
        table_type: Тип стола (например: 'standard', 'vip', 'window', 'outdoor')
        status: Текущий статус стола ('available', 'reserved', 'occupied')
        location: Расположение стола (например: 'main_hall', 'terrace', 'window_side')
        description: Дополнительное описание стола (опционально)
        is_active: Активен ли стол (можно временно отключить)
        created_at: Дата и время создания записи
        updated_at: Дата и время последнего обновления записи
    """
    id: Optional[int] = None
    table_number: str = ""
    capacity: int = 2  # По умолчанию стол на 2 персоны
    table_type: str = "standard"  # По умолчанию обычный стол
    status: str = "available"  # По умолчанию доступен
    location: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def get_table_name(cls) -> str:
        """Возвращает имя таблицы в базе данных"""
        return "restaurant_tables"
    
    @classmethod
    def get_create_table_sql(cls) -> str:
        """
        Возвращает SQL запрос для создания таблицы restaurant_tables.
        Можно использовать для миграций или инициализации БД.
        """
        return """
        CREATE TABLE IF NOT EXISTS restaurant_tables (
            id SERIAL PRIMARY KEY,
            table_number VARCHAR(50) UNIQUE NOT NULL,
            capacity INTEGER NOT NULL CHECK (capacity > 0),
            table_type VARCHAR(50) DEFAULT 'standard' NOT NULL,
            status VARCHAR(50) DEFAULT 'available' NOT NULL,
            location VARCHAR(100),
            description TEXT,
            is_active BOOLEAN DEFAULT TRUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_restaurant_tables_number ON restaurant_tables(table_number);
        CREATE INDEX IF NOT EXISTS idx_restaurant_tables_status ON restaurant_tables(status);
        CREATE INDEX IF NOT EXISTS idx_restaurant_tables_type ON restaurant_tables(table_type);
        CREATE INDEX IF NOT EXISTS idx_restaurant_tables_active ON restaurant_tables(is_active);
        """
    
    def to_dict(self) -> dict:
        """Преобразует объект стола в словарь для работы с БД"""
        return {
            'table_number': self.table_number,
            'capacity': self.capacity,
            'table_type': self.table_type,
            'status': self.status,
            'location': self.location,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RestaurantTable':
        """Создает объект стола из словаря (например, из результата БД)"""
        return cls(
            id=data.get('id'),
            table_number=data.get('table_number', ''),
            capacity=data.get('capacity', 2),
            table_type=data.get('table_type', 'standard'),
            status=data.get('status', 'available'),
            location=data.get('location'),
            description=data.get('description'),
            is_active=data.get('is_active', True),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
