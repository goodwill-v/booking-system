"""
Модель пользователя для системы бронирования
Содержит базовые поля, необходимые для работы с таблицей users
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """
    Модель пользователя системы бронирования.
    
    Поля:
        id: Уникальный идентификатор пользователя (первичный ключ)
        email: Email пользователя (уникальный, для входа в систему)
        password_hash: Хэшированный пароль
        full_name: Полное имя пользователя
        phone: Номер телефона для связи
        role: Роль пользователя (например: 'client', 'admin')
        is_active: Активен ли пользователь (для блокировки/разблокировки)
        created_at: Дата и время создания записи
        updated_at: Дата и время последнего обновления записи
    """
    id: Optional[int] = None
    email: str = ""
    password_hash: str = ""
    full_name: str = ""
    phone: Optional[str] = None
    role: str = "client"  # По умолчанию обычный клиент
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def get_table_name(cls) -> str:
        """Возвращает имя таблицы в базе данных"""
        return "users"
    
    @classmethod
    def get_create_table_sql(cls) -> str:
        """
        Возвращает SQL запрос для создания таблицы users.
        Можно использовать для миграций или инициализации БД.
        """
        return """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            phone VARCHAR(20),
            role VARCHAR(50) DEFAULT 'client' NOT NULL,
            is_active BOOLEAN DEFAULT TRUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
        """
    
    def to_dict(self) -> dict:
        """Преобразует объект пользователя в словарь для работы с БД"""
        return {
            'email': self.email,
            'password_hash': self.password_hash,
            'full_name': self.full_name,
            'phone': self.phone,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """Создает объект пользователя из словаря (например, из результата БД)"""
        return cls(
            id=data.get('id'),
            email=data.get('email', ''),
            password_hash=data.get('password_hash', ''),
            full_name=data.get('full_name', ''),
            phone=data.get('phone'),
            role=data.get('role', 'client'),
            is_active=data.get('is_active', True),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
