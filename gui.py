"""
Графический интерфейс для системы бронирования ресторана
Использует tkinter для создания GUI с вкладками
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime, date, time
from typing import Optional, List
import hashlib

from postgres_driver import PostgreSQLDriver
from backend import (
    # Users CRUD
    create_user, read_user, read_users, update_user, delete_user, get_all_users,
    # Tables CRUD
    create_table, read_table, read_tables, update_table, delete_table, get_all_tables,
    # Bookings CRUD
    create_booking, read_booking, read_bookings, update_booking, delete_booking, get_all_bookings,
    # Availability check
    check_table_availability
)
from models.users import User
from models.tables import RestaurantTable
from models.booking import Booking


class BookingSystemGUI:
    """Основной класс графического интерфейса системы бронирования"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Система бронирования ресторана")
        self.root.geometry("1000x700")
        
        # Создаем драйвер базы данных
        self.driver = PostgreSQLDriver()
        try:
            self.driver.connect()
        except Exception as e:
            messagebox.showerror("Ошибка подключения", f"Не удалось подключиться к базе данных:\n{e}")
            root.destroy()
            return
        
        # Создаем вкладки
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Вкладка управления пользователями
        self.users_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.users_frame, text="Пользователи")
        self._create_users_tab()
        
        # Вкладка управления столами
        self.tables_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.tables_frame, text="Столы")
        self._create_tables_tab()
        
        # Вкладка управления бронированиями
        self.bookings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.bookings_frame, text="Бронирования")
        self._create_bookings_tab()
        
        # Вкладка проверки доступности
        self.availability_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.availability_frame, text="Проверка доступности")
        self._create_availability_tab()
        
        # Обработчик закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_closing(self):
        """Обработчик закрытия приложения"""
        if self.driver:
            self.driver.disconnect()
        self.root.destroy()
    
    def _hash_password(self, password: str) -> str:
        """Хеширование пароля (простая реализация)"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    # ==================== ВКЛАДКА ПОЛЬЗОВАТЕЛЕЙ ====================
    
    def _create_users_tab(self):
        """Создает вкладку управления пользователями"""
        # Левая панель - форма
        left_frame = ttk.LabelFrame(self.users_frame, text="Форма пользователя", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # ID (только для чтения при обновлении)
        ttk.Label(left_frame, text="ID:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.user_id_var = tk.StringVar()
        ttk.Label(left_frame, textvariable=self.user_id_var, foreground="gray").grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # Email
        ttk.Label(left_frame, text="Email *:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.user_email_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.user_email_var, width=30).grid(row=1, column=1, pady=2)
        
        # Пароль
        ttk.Label(left_frame, text="Пароль *:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.user_password_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.user_password_var, show="*", width=30).grid(row=2, column=1, pady=2)
        
        # Полное имя
        ttk.Label(left_frame, text="Полное имя *:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.user_full_name_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.user_full_name_var, width=30).grid(row=3, column=1, pady=2)
        
        # Телефон
        ttk.Label(left_frame, text="Телефон:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.user_phone_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.user_phone_var, width=30).grid(row=4, column=1, pady=2)
        
        # Роль
        ttk.Label(left_frame, text="Роль:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.user_role_var = tk.StringVar(value="client")
        role_combo = ttk.Combobox(left_frame, textvariable=self.user_role_var, 
                                 values=["client", "admin"], width=27, state="readonly")
        role_combo.grid(row=5, column=1, pady=2)
        
        # Активен
        self.user_is_active_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(left_frame, text="Активен", variable=self.user_is_active_var).grid(row=6, column=0, columnspan=2, pady=2)
        
        # Кнопки
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Создать", command=self._create_user_action).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Обновить", command=self._update_user_action).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Удалить", command=self._delete_user_action).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Очистить", command=self._clear_user_form).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Обновить список", command=self._refresh_users_list).pack(side=tk.LEFT, padx=2)
        
        # Правая панель - список пользователей
        right_frame = ttk.LabelFrame(self.users_frame, text="Список пользователей", padding=10)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Таблица пользователей
        columns = ("ID", "Email", "Имя", "Телефон", "Роль", "Активен")
        self.users_tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=20)
        
        for col in columns:
            self.users_tree.heading(col, text=col)
            self.users_tree.column(col, width=100)
        
        scrollbar_users = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=scrollbar_users.set)
        
        self.users_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_users.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.users_tree.bind("<Double-1>", self._on_user_select)
        
        # Загружаем пользователей
        self._refresh_users_list()
    
    def _create_user_action(self):
        """Создает нового пользователя"""
        try:
            if not self.user_email_var.get() or not self.user_password_var.get() or not self.user_full_name_var.get():
                messagebox.showwarning("Предупреждение", "Заполните обязательные поля (Email, Пароль, Имя)")
                return
            
            user = User(
                email=self.user_email_var.get(),
                password_hash=self._hash_password(self.user_password_var.get()),
                full_name=self.user_full_name_var.get(),
                phone=self.user_phone_var.get() if self.user_phone_var.get() else None,
                role=self.user_role_var.get(),
                is_active=self.user_is_active_var.get()
            )
            
            user_id = create_user(user, self.driver)
            if user_id:
                messagebox.showinfo("Успех", f"Пользователь создан с ID: {user_id}")
                self._clear_user_form()
                self._refresh_users_list()
            else:
                messagebox.showerror("Ошибка", "Не удалось создать пользователя")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при создании пользователя:\n{e}")
    
    def _update_user_action(self):
        """Обновляет существующего пользователя"""
        try:
            if not self.user_id_var.get():
                messagebox.showwarning("Предупреждение", "Выберите пользователя для обновления")
                return
            
            user_id = int(self.user_id_var.get())
            
            # Читаем существующего пользователя для сохранения пароля если не изменен
            existing_user = read_user(user_id, self.driver)
            if not existing_user:
                messagebox.showerror("Ошибка", "Пользователь не найден")
                return
            
            password_hash = existing_user.password_hash
            # Если пароль введен, хешируем его
            if self.user_password_var.get():
                password_hash = self._hash_password(self.user_password_var.get())
            
            user = User(
                id=user_id,
                email=self.user_email_var.get(),
                password_hash=password_hash,
                full_name=self.user_full_name_var.get(),
                phone=self.user_phone_var.get() if self.user_phone_var.get() else None,
                role=self.user_role_var.get(),
                is_active=self.user_is_active_var.get()
            )
            
            if update_user(user_id, user, self.driver):
                messagebox.showinfo("Успех", "Пользователь обновлен")
                self._clear_user_form()
                self._refresh_users_list()
            else:
                messagebox.showerror("Ошибка", "Не удалось обновить пользователя")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при обновлении пользователя:\n{e}")
    
    def _delete_user_action(self):
        """Удаляет пользователя"""
        try:
            if not self.user_id_var.get():
                messagebox.showwarning("Предупреждение", "Выберите пользователя для удаления")
                return
            
            user_id = int(self.user_id_var.get())
            
            if messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите удалить пользователя с ID {user_id}?"):
                if delete_user(user_id, self.driver):
                    messagebox.showinfo("Успех", "Пользователь удален")
                    self._clear_user_form()
                    self._refresh_users_list()
                else:
                    messagebox.showerror("Ошибка", "Не удалось удалить пользователя")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при удалении пользователя:\n{e}")
    
    def _clear_user_form(self):
        """Очищает форму пользователя"""
        self.user_id_var.set("")
        self.user_email_var.set("")
        self.user_password_var.set("")
        self.user_full_name_var.set("")
        self.user_phone_var.set("")
        self.user_role_var.set("client")
        self.user_is_active_var.set(True)
    
    def _refresh_users_list(self):
        """Обновляет список пользователей"""
        try:
            # Очищаем таблицу
            for item in self.users_tree.get_children():
                self.users_tree.delete(item)
            
            # Загружаем пользователей
            users = get_all_users(self.driver)
            for user in users:
                self.users_tree.insert("", tk.END, values=(
                    user.id,
                    user.email,
                    user.full_name,
                    user.phone or "",
                    user.role,
                    "Да" if user.is_active else "Нет"
                ))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке пользователей:\n{e}")
    
    def _on_user_select(self, event):
        """Обработчик двойного клика по пользователю"""
        selection = self.users_tree.selection()
        if selection:
            item = self.users_tree.item(selection[0])
            user_id = item['values'][0]
            
            try:
                user = read_user(user_id, self.driver)
                if user:
                    self.user_id_var.set(str(user.id))
                    self.user_email_var.set(user.email)
                    self.user_password_var.set("")  # Не показываем пароль
                    self.user_full_name_var.set(user.full_name)
                    self.user_phone_var.set(user.phone or "")
                    self.user_role_var.set(user.role)
                    self.user_is_active_var.set(user.is_active)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при загрузке пользователя:\n{e}")
    
    # ==================== ВКЛАДКА СТОЛОВ ====================
    
    def _create_tables_tab(self):
        """Создает вкладку управления столами"""
        # Левая панель - форма
        left_frame = ttk.LabelFrame(self.tables_frame, text="Форма стола", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # ID
        ttk.Label(left_frame, text="ID:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.table_id_var = tk.StringVar()
        ttk.Label(left_frame, textvariable=self.table_id_var, foreground="gray").grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # Номер стола
        ttk.Label(left_frame, text="Номер стола *:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.table_number_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.table_number_var, width=30).grid(row=1, column=1, pady=2)
        
        # Вместимость
        ttk.Label(left_frame, text="Вместимость *:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.table_capacity_var = tk.StringVar(value="2")
        ttk.Spinbox(left_frame, textvariable=self.table_capacity_var, from_=1, to=20, width=27).grid(row=2, column=1, pady=2)
        
        # Тип стола
        ttk.Label(left_frame, text="Тип стола:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.table_type_var = tk.StringVar(value="standard")
        type_combo = ttk.Combobox(left_frame, textvariable=self.table_type_var,
                                 values=["standard", "vip", "window", "outdoor"], width=27, state="readonly")
        type_combo.grid(row=3, column=1, pady=2)
        
        # Статус
        ttk.Label(left_frame, text="Статус:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.table_status_var = tk.StringVar(value="available")
        status_combo = ttk.Combobox(left_frame, textvariable=self.table_status_var,
                                   values=["available", "reserved", "occupied"], width=27, state="readonly")
        status_combo.grid(row=4, column=1, pady=2)
        
        # Расположение
        ttk.Label(left_frame, text="Расположение:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.table_location_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.table_location_var, width=30).grid(row=5, column=1, pady=2)
        
        # Описание
        ttk.Label(left_frame, text="Описание:").grid(row=6, column=0, sticky=tk.W, pady=2)
        self.table_description_text = scrolledtext.ScrolledText(left_frame, width=30, height=3)
        self.table_description_text.grid(row=6, column=1, pady=2)
        
        # Активен
        self.table_is_active_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(left_frame, text="Активен", variable=self.table_is_active_var).grid(row=7, column=0, columnspan=2, pady=2)
        
        # Кнопки
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Создать", command=self._create_table_action).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Обновить", command=self._update_table_action).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Удалить", command=self._delete_table_action).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Очистить", command=self._clear_table_form).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Обновить список", command=self._refresh_tables_list).pack(side=tk.LEFT, padx=2)
        
        # Правая панель - список столов
        right_frame = ttk.LabelFrame(self.tables_frame, text="Список столов", padding=10)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Таблица столов
        columns = ("ID", "Номер", "Вместимость", "Тип", "Статус", "Расположение", "Активен")
        self.tables_tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=20)
        
        for col in columns:
            self.tables_tree.heading(col, text=col)
            self.tables_tree.column(col, width=100)
        
        scrollbar_tables = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.tables_tree.yview)
        self.tables_tree.configure(yscrollcommand=scrollbar_tables.set)
        
        self.tables_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_tables.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tables_tree.bind("<Double-1>", self._on_table_select)
        
        # Загружаем столы
        self._refresh_tables_list()
    
    def _create_table_action(self):
        """Создает новый стол"""
        try:
            if not self.table_number_var.get():
                messagebox.showwarning("Предупреждение", "Заполните номер стола")
                return
            
            table = RestaurantTable(
                table_number=self.table_number_var.get(),
                capacity=int(self.table_capacity_var.get()),
                table_type=self.table_type_var.get(),
                status=self.table_status_var.get(),
                location=self.table_location_var.get() if self.table_location_var.get() else None,
                description=self.table_description_text.get("1.0", tk.END).strip() or None,
                is_active=self.table_is_active_var.get()
            )
            
            table_id = create_table(table, self.driver)
            if table_id:
                messagebox.showinfo("Успех", f"Стол создан с ID: {table_id}")
                self._clear_table_form()
                self._refresh_tables_list()
            else:
                messagebox.showerror("Ошибка", "Не удалось создать стол")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при создании стола:\n{e}")
    
    def _update_table_action(self):
        """Обновляет существующий стол"""
        try:
            if not self.table_id_var.get():
                messagebox.showwarning("Предупреждение", "Выберите стол для обновления")
                return
            
            table_id = int(self.table_id_var.get())
            
            table = RestaurantTable(
                id=table_id,
                table_number=self.table_number_var.get(),
                capacity=int(self.table_capacity_var.get()),
                table_type=self.table_type_var.get(),
                status=self.table_status_var.get(),
                location=self.table_location_var.get() if self.table_location_var.get() else None,
                description=self.table_description_text.get("1.0", tk.END).strip() or None,
                is_active=self.table_is_active_var.get()
            )
            
            if update_table(table_id, table, self.driver):
                messagebox.showinfo("Успех", "Стол обновлен")
                self._clear_table_form()
                self._refresh_tables_list()
            else:
                messagebox.showerror("Ошибка", "Не удалось обновить стол")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при обновлении стола:\n{e}")
    
    def _delete_table_action(self):
        """Удаляет стол"""
        try:
            if not self.table_id_var.get():
                messagebox.showwarning("Предупреждение", "Выберите стол для удаления")
                return
            
            table_id = int(self.table_id_var.get())
            
            if messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите удалить стол с ID {table_id}?"):
                if delete_table(table_id, self.driver):
                    messagebox.showinfo("Успех", "Стол удален")
                    self._clear_table_form()
                    self._refresh_tables_list()
                else:
                    messagebox.showerror("Ошибка", "Не удалось удалить стол")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при удалении стола:\n{e}")
    
    def _clear_table_form(self):
        """Очищает форму стола"""
        self.table_id_var.set("")
        self.table_number_var.set("")
        self.table_capacity_var.set("2")
        self.table_type_var.set("standard")
        self.table_status_var.set("available")
        self.table_location_var.set("")
        self.table_description_text.delete("1.0", tk.END)
        self.table_is_active_var.set(True)
    
    def _refresh_tables_list(self):
        """Обновляет список столов"""
        try:
            # Очищаем таблицу
            for item in self.tables_tree.get_children():
                self.tables_tree.delete(item)
            
            # Загружаем столы
            tables = get_all_tables(self.driver)
            for table in tables:
                self.tables_tree.insert("", tk.END, values=(
                    table.id,
                    table.table_number,
                    table.capacity,
                    table.table_type,
                    table.status,
                    table.location or "",
                    "Да" if table.is_active else "Нет"
                ))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке столов:\n{e}")
    
    def _on_table_select(self, event):
        """Обработчик двойного клика по столу"""
        selection = self.tables_tree.selection()
        if selection:
            item = self.tables_tree.item(selection[0])
            table_id = item['values'][0]
            
            try:
                table = read_table(table_id, self.driver)
                if table:
                    self.table_id_var.set(str(table.id))
                    self.table_number_var.set(table.table_number)
                    self.table_capacity_var.set(str(table.capacity))
                    self.table_type_var.set(table.table_type)
                    self.table_status_var.set(table.status)
                    self.table_location_var.set(table.location or "")
                    self.table_description_text.delete("1.0", tk.END)
                    if table.description:
                        self.table_description_text.insert("1.0", table.description)
                    self.table_is_active_var.set(table.is_active)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при загрузке стола:\n{e}")
    
    # ==================== ВКЛАДКА БРОНИРОВАНИЙ ====================
    
    def _create_bookings_tab(self):
        """Создает вкладку управления бронированиями"""
        # Левая панель - форма
        left_frame = ttk.LabelFrame(self.bookings_frame, text="Форма бронирования", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # ID
        ttk.Label(left_frame, text="ID:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.booking_id_var = tk.StringVar()
        ttk.Label(left_frame, textvariable=self.booking_id_var, foreground="gray").grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # ID пользователя
        ttk.Label(left_frame, text="ID пользователя *:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.booking_user_id_var = tk.StringVar()
        user_frame = ttk.Frame(left_frame)
        user_frame.grid(row=1, column=1, sticky=tk.W, pady=2)
        ttk.Entry(user_frame, textvariable=self.booking_user_id_var, width=20).pack(side=tk.LEFT)
        ttk.Button(user_frame, text="...", command=self._select_user_for_booking, width=3).pack(side=tk.LEFT, padx=2)
        
        # ID стола
        ttk.Label(left_frame, text="ID стола *:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.booking_table_id_var = tk.StringVar()
        table_frame = ttk.Frame(left_frame)
        table_frame.grid(row=2, column=1, sticky=tk.W, pady=2)
        ttk.Entry(table_frame, textvariable=self.booking_table_id_var, width=20).pack(side=tk.LEFT)
        ttk.Button(table_frame, text="...", command=self._select_table_for_booking, width=3).pack(side=tk.LEFT, padx=2)
        
        # Дата бронирования
        ttk.Label(left_frame, text="Дата бронирования *:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.booking_date_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.booking_date_var, width=30).grid(row=3, column=1, pady=2)
        ttk.Label(left_frame, text="(YYYY-MM-DD)", foreground="gray", font=("Arial", 8)).grid(row=4, column=1, sticky=tk.W)
        
        # Время начала
        ttk.Label(left_frame, text="Время начала *:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.booking_time_start_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.booking_time_start_var, width=30).grid(row=5, column=1, pady=2)
        ttk.Label(left_frame, text="(HH:MM)", foreground="gray", font=("Arial", 8)).grid(row=6, column=1, sticky=tk.W)
        
        # Время окончания
        ttk.Label(left_frame, text="Время окончания *:").grid(row=7, column=0, sticky=tk.W, pady=2)
        self.booking_time_end_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.booking_time_end_var, width=30).grid(row=7, column=1, pady=2)
        ttk.Label(left_frame, text="(HH:MM)", foreground="gray", font=("Arial", 8)).grid(row=8, column=1, sticky=tk.W)
        
        # Количество гостей
        ttk.Label(left_frame, text="Количество гостей *:").grid(row=9, column=0, sticky=tk.W, pady=2)
        self.booking_guests_var = tk.StringVar(value="1")
        ttk.Spinbox(left_frame, textvariable=self.booking_guests_var, from_=1, to=20, width=27).grid(row=9, column=1, pady=2)
        
        # Статус
        ttk.Label(left_frame, text="Статус:").grid(row=10, column=0, sticky=tk.W, pady=2)
        self.booking_status_var = tk.StringVar(value="pending")
        status_combo = ttk.Combobox(left_frame, textvariable=self.booking_status_var,
                                   values=["pending", "confirmed", "cancelled", "completed"], width=27, state="readonly")
        status_combo.grid(row=10, column=1, pady=2)
        
        # Заметки
        ttk.Label(left_frame, text="Заметки:").grid(row=11, column=0, sticky=tk.W, pady=2)
        self.booking_notes_text = scrolledtext.ScrolledText(left_frame, width=30, height=3)
        self.booking_notes_text.grid(row=11, column=1, pady=2)
        
        # Кнопки
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=12, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Создать", command=self._create_booking_action).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Обновить", command=self._update_booking_action).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Удалить", command=self._delete_booking_action).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Очистить", command=self._clear_booking_form).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Обновить список", command=self._refresh_bookings_list).pack(side=tk.LEFT, padx=2)
        
        # Правая панель - список бронирований
        right_frame = ttk.LabelFrame(self.bookings_frame, text="Список бронирований", padding=10)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Таблица бронирований
        columns = ("ID", "Пользователь", "Стол", "Дата", "Время", "Гости", "Статус")
        self.bookings_tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=20)
        
        for col in columns:
            self.bookings_tree.heading(col, text=col)
            self.bookings_tree.column(col, width=100)
        
        scrollbar_bookings = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.bookings_tree.yview)
        self.bookings_tree.configure(yscrollcommand=scrollbar_bookings.set)
        
        self.bookings_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_bookings.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.bookings_tree.bind("<Double-1>", self._on_booking_select)
        
        # Загружаем бронирования
        self._refresh_bookings_list()
    
    def _select_user_for_booking(self):
        """Открывает диалог выбора пользователя"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Выбор пользователя")
        dialog.geometry("400x300")
        
        ttk.Label(dialog, text="Выберите пользователя:").pack(pady=5)
        
        user_listbox = tk.Listbox(dialog, height=10)
        user_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        users = get_all_users(self.driver)
        for user in users:
            user_listbox.insert(tk.END, f"ID: {user.id} - {user.full_name} ({user.email})")
        
        def select_user():
            selection = user_listbox.curselection()
            if selection:
                user = users[selection[0]]
                self.booking_user_id_var.set(str(user.id))
                dialog.destroy()
        
        ttk.Button(dialog, text="Выбрать", command=select_user).pack(pady=5)
    
    def _select_table_for_booking(self):
        """Открывает диалог выбора стола"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Выбор стола")
        dialog.geometry("400x300")
        
        ttk.Label(dialog, text="Выберите стол:").pack(pady=5)
        
        table_listbox = tk.Listbox(dialog, height=10)
        table_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        tables = get_all_tables(self.driver)
        for table in tables:
            table_listbox.insert(tk.END, f"ID: {table.id} - Стол {table.table_number} (вместимость: {table.capacity})")
        
        def select_table():
            selection = table_listbox.curselection()
            if selection:
                table = tables[selection[0]]
                self.booking_table_id_var.set(str(table.id))
                dialog.destroy()
        
        ttk.Button(dialog, text="Выбрать", command=select_table).pack(pady=5)
    
    def _create_booking_action(self):
        """Создает новое бронирование"""
        try:
            if not all([self.booking_user_id_var.get(), self.booking_table_id_var.get(),
                       self.booking_date_var.get(), self.booking_time_start_var.get(), 
                       self.booking_time_end_var.get()]):
                messagebox.showwarning("Предупреждение", "Заполните все обязательные поля")
                return
            
            # Парсим дату и время
            booking_date = datetime.strptime(self.booking_date_var.get(), "%Y-%m-%d").date()
            booking_time_start_str = self.booking_time_start_var.get()
            if len(booking_time_start_str) == 5:  # HH:MM
                booking_time_start = datetime.strptime(booking_time_start_str, "%H:%M").time()
            else:
                booking_time_start = datetime.strptime(booking_time_start_str, "%H:%M:%S").time()
            
            booking_time_end_str = self.booking_time_end_var.get()
            if len(booking_time_end_str) == 5:  # HH:MM
                booking_time_end = datetime.strptime(booking_time_end_str, "%H:%M").time()
            else:
                booking_time_end = datetime.strptime(booking_time_end_str, "%H:%M:%S").time()
            
            # Валидация времени окончания должно быть позже времени начала
            if booking_time_start >= booking_time_end:
                messagebox.showwarning("Предупреждение", "Время окончания должно быть позже времени начала")
                return
            
            booking_time_dt = datetime.combine(date.today(), booking_time_start)
            booking_time_end_dt = datetime.combine(date.today(), booking_time_end)
            
            booking = Booking(
                user_id=int(self.booking_user_id_var.get()),
                table_id=int(self.booking_table_id_var.get()),
                booking_date=booking_date,
                booking_time=booking_time_dt,
                booking_end_time=booking_time_end_dt,
                number_of_guests=int(self.booking_guests_var.get()),
                status=self.booking_status_var.get(),
                notes=self.booking_notes_text.get("1.0", tk.END).strip() or None
            )
            
            # Создаем бронирование (проверка доступности выполняется внутри create_booking)
            booking_id = create_booking(booking, self.driver)
            if booking_id:
                messagebox.showinfo("Успех", f"Бронирование создано с ID: {booking_id}")
                self._clear_booking_form()
                self._refresh_bookings_list()
            else:
                # Сообщение об ошибке уже выведено в create_booking
                messagebox.showerror("Ошибка", 
                    "Не удалось создать бронирование.\n"
                    "Возможные причины:\n"
                    "- Стол не существует или неактивен\n"
                    "- Стол уже забронирован на это время\n"
                    "- Время бронирования пересекается с существующим бронированием")
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Неверный формат даты или времени:\n{e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при создании бронирования:\n{e}")
    
    def _update_booking_action(self):
        """Обновляет существующее бронирование"""
        try:
            if not self.booking_id_var.get():
                messagebox.showwarning("Предупреждение", "Выберите бронирование для обновления")
                return
            
            booking_id = int(self.booking_id_var.get())
            
            # Валидация времени окончания должно быть позже времени начала
            if not all([self.booking_time_start_var.get(), self.booking_time_end_var.get()]):
                messagebox.showwarning("Предупреждение", "Заполните время начала и окончания")
                return
            
            # Парсим дату и время
            booking_date = datetime.strptime(self.booking_date_var.get(), "%Y-%m-%d").date()
            booking_time_start_str = self.booking_time_start_var.get()
            if len(booking_time_start_str) == 5:  # HH:MM
                booking_time_start = datetime.strptime(booking_time_start_str, "%H:%M").time()
            else:
                booking_time_start = datetime.strptime(booking_time_start_str, "%H:%M:%S").time()
            
            # Валидация времени окончания должно быть позже времени начала
            booking_time_end_str = self.booking_time_end_var.get()
            if len(booking_time_end_str) == 5:  # HH:MM
                booking_time_end = datetime.strptime(booking_time_end_str, "%H:%M").time()
            else:
                booking_time_end = datetime.strptime(booking_time_end_str, "%H:%M:%S").time()
            
            if booking_time_start >= booking_time_end:
                messagebox.showwarning("Предупреждение", "Время окончания должно быть позже времени начала")
                return
            
            booking_time_dt = datetime.combine(date.today(), booking_time_start)
            booking_time_end_dt = datetime.combine(date.today(), booking_time_end)
            
            booking = Booking(
                id=booking_id,
                user_id=int(self.booking_user_id_var.get()),
                table_id=int(self.booking_table_id_var.get()),
                booking_date=booking_date,
                booking_time=booking_time_dt,
                booking_end_time=booking_time_end_dt,
                number_of_guests=int(self.booking_guests_var.get()),
                status=self.booking_status_var.get(),
                notes=self.booking_notes_text.get("1.0", tk.END).strip() or None
            )
            
            # Обновляем бронирование (проверка доступности выполняется внутри update_booking)
            if update_booking(booking_id, booking, self.driver):
                messagebox.showinfo("Успех", "Бронирование обновлено")
                self._clear_booking_form()
                self._refresh_bookings_list()
            else:
                # Сообщение об ошибке уже выведено в update_booking
                messagebox.showerror("Ошибка", 
                    "Не удалось обновить бронирование.\n"
                    "Возможные причины:\n"
                    "- Стол не существует или неактивен\n"
                    "- Стол уже забронирован на это время другим пользователем\n"
                    "- Время бронирования пересекается с существующим бронированием")
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Неверный формат даты или времени:\n{e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при обновлении бронирования:\n{e}")
    
    def _delete_booking_action(self):
        """Удаляет бронирование"""
        try:
            if not self.booking_id_var.get():
                messagebox.showwarning("Предупреждение", "Выберите бронирование для удаления")
                return
            
            booking_id = int(self.booking_id_var.get())
            
            if messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите удалить бронирование с ID {booking_id}?"):
                if delete_booking(booking_id, self.driver):
                    messagebox.showinfo("Успех", "Бронирование удалено")
                    self._clear_booking_form()
                    self._refresh_bookings_list()
                else:
                    messagebox.showerror("Ошибка", "Не удалось удалить бронирование")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при удалении бронирования:\n{e}")
    
    def _clear_booking_form(self):
        """Очищает форму бронирования"""
        self.booking_id_var.set("")
        self.booking_user_id_var.set("")
        self.booking_table_id_var.set("")
        self.booking_date_var.set("")
        self.booking_time_start_var.set("")
        self.booking_time_end_var.set("")
        self.booking_guests_var.set("1")
        self.booking_status_var.set("pending")
        self.booking_notes_text.delete("1.0", tk.END)
    
    def _refresh_bookings_list(self):
        """Обновляет список бронирований"""
        try:
            # Очищаем таблицу
            for item in self.bookings_tree.get_children():
                self.bookings_tree.delete(item)
            
            # Загружаем бронирования
            bookings = get_all_bookings(self.driver)
            for booking in bookings:
                # Получаем информацию о пользователе и столе
                user = read_user(booking.user_id, self.driver)
                table = read_table(booking.table_id, self.driver)
                
                user_name = user.full_name if user else f"ID:{booking.user_id}"
                table_number = table.table_number if table else f"ID:{booking.table_id}"
                
                booking_date_str = ""
                booking_time_str = ""
                if booking.booking_date:
                    if isinstance(booking.booking_date, date):
                        booking_date_str = booking.booking_date.strftime("%Y-%m-%d")
                    else:
                        booking_date_str = str(booking.booking_date)
                
                if booking.booking_time:
                    if isinstance(booking.booking_time, datetime):
                        booking_time_str = booking.booking_time.strftime("%H:%M")
                    elif isinstance(booking.booking_time, time):
                        booking_time_str = booking.booking_time.strftime("%H:%M")
                    else:
                        booking_time_str = str(booking.booking_time)
                
                self.bookings_tree.insert("", tk.END, values=(
                    booking.id,
                    user_name,
                    table_number,
                    booking_date_str,
                    booking_time_str,
                    booking.number_of_guests,
                    booking.status
                ))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке бронирований:\n{e}")
    
    def _on_booking_select(self, event):
        """Обработчик двойного клика по бронированию"""
        selection = self.bookings_tree.selection()
        if selection:
            item = self.bookings_tree.item(selection[0])
            booking_id = item['values'][0]
            
            try:
                booking = read_booking(booking_id, self.driver)
                if booking:
                    self.booking_id_var.set(str(booking.id))
                    self.booking_user_id_var.set(str(booking.user_id))
                    self.booking_table_id_var.set(str(booking.table_id))
                    
                    if booking.booking_date:
                        if isinstance(booking.booking_date, date):
                            self.booking_date_var.set(booking.booking_date.strftime("%Y-%m-%d"))
                        else:
                            self.booking_date_var.set(str(booking.booking_date))
                    
                    if booking.booking_time:
                        # Извлекаем время начала
                        if isinstance(booking.booking_time, datetime):
                            booking_time_obj = booking.booking_time.time()
                        elif isinstance(booking.booking_time, time):
                            booking_time_obj = booking.booking_time
                        else:
                            # Пытаемся преобразовать строку
                            try:
                                booking_time_obj = datetime.strptime(str(booking.booking_time), "%H:%M:%S").time()
                            except:
                                booking_time_obj = datetime.strptime(str(booking.booking_time), "%H:%M").time()
                        
                        # Устанавливаем время начала
                        self.booking_time_start_var.set(booking_time_obj.strftime("%H:%M"))
                    
                    # Извлекаем время окончания
                    if booking.booking_end_time:
                        # Извлекаем время окончания из базы данных
                        if isinstance(booking.booking_end_time, datetime):
                            booking_end_time_obj = booking.booking_end_time.time()
                        elif isinstance(booking.booking_end_time, time):
                            booking_end_time_obj = booking.booking_end_time
                        else:
                            # Пытаемся преобразовать строку
                            try:
                                booking_end_time_obj = datetime.strptime(str(booking.booking_end_time), "%H:%M:%S").time()
                            except:
                                booking_end_time_obj = datetime.strptime(str(booking.booking_end_time), "%H:%M").time()
                        
                        # Устанавливаем время окончания
                        self.booking_time_end_var.set(booking_end_time_obj.strftime("%H:%M"))
                    else:
                        # Если booking_end_time не задано, вычисляем его как время начала + 2 часа (для обратной совместимости)
                        if booking.booking_time:
                            from datetime import timedelta
                            booking_datetime = datetime.combine(date.today(), booking_time_obj)
                            booking_end_datetime = booking_datetime + timedelta(hours=2)
                            self.booking_time_end_var.set(booking_end_datetime.time().strftime("%H:%M"))
                    
                    self.booking_guests_var.set(str(booking.number_of_guests))
                    self.booking_status_var.set(booking.status)
                    self.booking_notes_text.delete("1.0", tk.END)
                    if booking.notes:
                        self.booking_notes_text.insert("1.0", booking.notes)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при загрузке бронирования:\n{e}")
    
    # ==================== ВКЛАДКА ПРОВЕРКИ ДОСТУПНОСТИ ====================
    
    def _create_availability_tab(self):
        """Создает вкладку проверки доступности столов"""
        main_frame = ttk.Frame(self.availability_frame, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        ttk.Label(main_frame, text="Проверка доступности стола", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        # Форма ввода параметров
        form_frame = ttk.LabelFrame(main_frame, text="Параметры проверки", padding=10)
        form_frame.pack(fill=tk.X, pady=10)
        
        # ID стола
        table_id_frame = ttk.Frame(form_frame)
        table_id_frame.pack(fill=tk.X, pady=5)
        ttk.Label(table_id_frame, text="ID стола *:", width=20).pack(side=tk.LEFT)
        self.availability_table_id_var = tk.StringVar()
        table_id_entry = ttk.Entry(table_id_frame, textvariable=self.availability_table_id_var, width=30)
        table_id_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(table_id_frame, text="...", command=self._select_table_for_availability, width=3).pack(side=tk.LEFT)
        
        # Дата бронирования
        date_frame = ttk.Frame(form_frame)
        date_frame.pack(fill=tk.X, pady=5)
        ttk.Label(date_frame, text="Дата бронирования *:", width=20).pack(side=tk.LEFT)
        self.availability_date_var = tk.StringVar()
        ttk.Entry(date_frame, textvariable=self.availability_date_var, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Label(date_frame, text="(YYYY-MM-DD)", foreground="gray", font=("Arial", 8)).pack(side=tk.LEFT)
        
        # Время начала
        time_start_frame = ttk.Frame(form_frame)
        time_start_frame.pack(fill=tk.X, pady=5)
        ttk.Label(time_start_frame, text="Время начала *:", width=20).pack(side=tk.LEFT)
        self.availability_time_start_var = tk.StringVar()
        ttk.Entry(time_start_frame, textvariable=self.availability_time_start_var, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Label(time_start_frame, text="(HH:MM)", foreground="gray", font=("Arial", 8)).pack(side=tk.LEFT)
        
        # Время окончания
        time_end_frame = ttk.Frame(form_frame)
        time_end_frame.pack(fill=tk.X, pady=5)
        ttk.Label(time_end_frame, text="Время окончания *:", width=20).pack(side=tk.LEFT)
        self.availability_time_end_var = tk.StringVar()
        ttk.Entry(time_end_frame, textvariable=self.availability_time_end_var, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Label(time_end_frame, text="(HH:MM)", foreground="gray", font=("Arial", 8)).pack(side=tk.LEFT)
        
        # ID бронирования для исключения (опционально, для обновления)
        exclude_frame = ttk.Frame(form_frame)
        exclude_frame.pack(fill=tk.X, pady=5)
        ttk.Label(exclude_frame, text="Исключить бронирование ID:", width=20).pack(side=tk.LEFT)
        self.availability_exclude_var = tk.StringVar()
        ttk.Entry(exclude_frame, textvariable=self.availability_exclude_var, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Label(exclude_frame, text="(опционально, для обновления)", foreground="gray", 
                 font=("Arial", 8)).pack(side=tk.LEFT)
        
        # КНОПКА ПРОВЕРКИ ДОСТУПНОСТИ (ОБЯЗАТЕЛЬНАЯ)
        check_button = ttk.Button(form_frame, text="Проверить доступность", 
                                 command=self._check_availability_action,
                                 width=30)
        check_button.pack(pady=20)
        
        # Область результатов
        result_frame = ttk.LabelFrame(main_frame, text="Результат проверки", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.availability_result_text = scrolledtext.ScrolledText(result_frame, 
                                                                  width=80, height=15,
                                                                  wrap=tk.WORD, state=tk.DISABLED)
        self.availability_result_text.pack(fill=tk.BOTH, expand=True)
    
    def _select_table_for_availability(self):
        """Открывает диалог выбора стола для проверки доступности"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Выбор стола")
        dialog.geometry("400x300")
        
        ttk.Label(dialog, text="Выберите стол:").pack(pady=5)
        
        table_listbox = tk.Listbox(dialog, height=10)
        table_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        tables = get_all_tables(self.driver)
        for table in tables:
            table_listbox.insert(tk.END, f"ID: {table.id} - Стол {table.table_number} (вместимость: {table.capacity})")
        
        def select_table():
            selection = table_listbox.curselection()
            if selection:
                table = tables[selection[0]]
                self.availability_table_id_var.set(str(table.id))
                dialog.destroy()
        
        ttk.Button(dialog, text="Выбрать", command=select_table).pack(pady=5)
    
    def _check_availability_action(self):
        """Выполняет проверку доступности стола"""
        try:
            # Валидация входных данных
            if not self.availability_table_id_var.get():
                messagebox.showwarning("Предупреждение", "Введите ID стола")
                return
            
            if not self.availability_date_var.get():
                messagebox.showwarning("Предупреждение", "Введите дату бронирования")
                return
            
            if not self.availability_time_start_var.get():
                messagebox.showwarning("Предупреждение", "Введите время начала бронирования")
                return
            
            if not self.availability_time_end_var.get():
                messagebox.showwarning("Предупреждение", "Введите время окончания бронирования")
                return
            
            # Парсим входные данные
            table_id = int(self.availability_table_id_var.get())
            booking_date = datetime.strptime(self.availability_date_var.get(), "%Y-%m-%d").date()
            
            booking_time_start_str = self.availability_time_start_var.get()
            if len(booking_time_start_str) == 5:  # HH:MM
                booking_time_start = datetime.strptime(booking_time_start_str, "%H:%M").time()
            else:
                booking_time_start = datetime.strptime(booking_time_start_str, "%H:%M:%S").time()
            
            booking_time_end_str = self.availability_time_end_var.get()
            if len(booking_time_end_str) == 5:  # HH:MM
                booking_time_end = datetime.strptime(booking_time_end_str, "%H:%M").time()
            else:
                booking_time_end = datetime.strptime(booking_time_end_str, "%H:%M:%S").time()
            
            # Валидация времени окончания должно быть позже времени начала
            if booking_time_start >= booking_time_end:
                messagebox.showwarning("Предупреждение", "Время окончания должно быть позже времени начала")
                return
            
            exclude_booking_id = None
            if self.availability_exclude_var.get():
                exclude_booking_id = int(self.availability_exclude_var.get())
            
            # Выполняем проверку
            result = check_table_availability(
                table_id=table_id,
                booking_date=booking_date,
                booking_time=booking_time_start,
                booking_end_time=booking_time_end,
                driver=self.driver,
                exclude_booking_id=exclude_booking_id
            )
            
            # Отображаем результаты
            self.availability_result_text.config(state=tk.NORMAL)
            self.availability_result_text.delete("1.0", tk.END)
            
            output = []
            output.append("=" * 60)
            output.append("РЕЗУЛЬТАТЫ ПРОВЕРКИ ДОСТУПНОСТИ СТОЛА")
            output.append("=" * 60)
            output.append("")
            
            # Информация о запросе
            output.append(f"ID стола: {table_id}")
            output.append(f"Дата бронирования: {booking_date}")
            output.append(f"Время начала: {booking_time_start}")
            output.append(f"Время окончания: {booking_time_end}")
            output.append("")
            
            # Результаты проверки
            output.append("Результат проверки:")
            output.append("-" * 60)
            
            if not result['table_exists']:
                output.append("❌ ОШИБКА: Стол с указанным ID не существует в базе данных")
            elif not result['table_active']:
                output.append("❌ ОШИБКА: Стол существует, но неактивен")
                output.append("   (Стол временно недоступен для бронирования)")
            elif result['available']:
                output.append("✅ СТОЛ ДОСТУПЕН")
                output.append("")
                output.append("Стол свободен на указанное время и может быть забронирован.")
            else:
                output.append("❌ СТОЛ НЕДОСТУПЕН")
                output.append("")
                output.append("Стол уже забронирован на это время или время пересекается с существующим бронированием.")
                
                if result['conflicting_booking']:
                    conflict = result['conflicting_booking']
                    output.append("")
                    output.append("Конфликтующее бронирование:")
                    output.append(f"  ID бронирования: {conflict.id}")
                    output.append(f"  Пользователь ID: {conflict.user_id}")
                    
                    # Получаем информацию о пользователе
                    user = read_user(conflict.user_id, self.driver)
                    if user:
                        output.append(f"  Пользователь: {user.full_name} ({user.email})")
                    
                    if conflict.booking_time:
                        if isinstance(conflict.booking_time, datetime):
                            conflict_time_start = conflict.booking_time.strftime("%H:%M")
                        elif isinstance(conflict.booking_time, time):
                            conflict_time_start = conflict.booking_time.strftime("%H:%M")
                        else:
                            conflict_time_start = str(conflict.booking_time)
                        output.append(f"  Время начала: {conflict_time_start}")
                    
                    if conflict.booking_end_time:
                        if isinstance(conflict.booking_end_time, datetime):
                            conflict_time_end = conflict.booking_end_time.strftime("%H:%M")
                        elif isinstance(conflict.booking_end_time, time):
                            conflict_time_end = conflict.booking_end_time.strftime("%H:%M")
                        else:
                            conflict_time_end = str(conflict.booking_end_time)
                        output.append(f"  Время окончания: {conflict_time_end}")
                    elif conflict.booking_time:
                        # Если booking_end_time не задано, вычисляем его (для обратной совместимости)
                        output.append(f"  Время окончания: (не указано, используется 2 часа)")
                    
                    if conflict.status:
                        output.append(f"  Статус: {conflict.status}")
            
            output.append("")
            output.append("=" * 60)
            
            result_text = "\n".join(output)
            self.availability_result_text.insert("1.0", result_text)
            self.availability_result_text.config(state=tk.DISABLED)
            
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Неверный формат данных:\n{e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при проверке доступности:\n{e}")
            self.availability_result_text.config(state=tk.NORMAL)
            self.availability_result_text.delete("1.0", tk.END)
            self.availability_result_text.insert("1.0", f"Ошибка: {str(e)}")
            self.availability_result_text.config(state=tk.DISABLED)


def main():
    """Главная функция для запуска GUI"""
    root = tk.Tk()
    app = BookingSystemGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
