#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import requests
import json
from datetime import datetime, timedelta
import os
import threading
import calendar
from tkinter import font

class ModernScheduleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CampusConnect - Расписание СПбПУ")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f5f7f8')
        
        # Цветовая схема
        self.colors = {
            'primary': '#0d7ff2',
            'bg_light': '#f5f7f8',
            'bg_dark': '#101922',
            'text_primary': '#101922',
            'text_secondary': '#6b7280',
            'border': '#e5e7eb',
            'card_bg': '#ffffff',
            'current_class': '#f97316',
            'success': '#10b981',
            'error': '#ef4444'
        }
        
        # Файл конфигурации
        self.config_file = os.path.expanduser("~/.schedule_config")
        
        # Переменные
        self.group_id = self.load_group_id()
        self.current_date = self.get_monday_of_week(datetime.now())
        self.selected_date = self.current_date
        self.view_mode = 'daily'  # daily или weekly
        
        # Настраиваем шрифты
        self.setup_fonts()
        
        # Создаем интерфейс
        self.create_modern_interface()
        
        # Если группа не настроена, показываем диалог
        if not self.group_id:
            self.setup_group()
        else:
            self.load_schedule()
    
    def setup_fonts(self):
        """Настройка шрифтов в стиле Web UI"""
        try:
            self.font_title = font.Font(family="SF Pro Display", size=28, weight="bold")
            self.font_header = font.Font(family="SF Pro Display", size=20, weight="bold")
            self.font_subheader = font.Font(family="SF Pro Display", size=16, weight="600")
            self.font_body = font.Font(family="SF Pro Text", size=14)
            self.font_small = font.Font(family="SF Pro Text", size=12)
            self.font_tiny = font.Font(family="SF Pro Text", size=10)
        except:
            self.font_title = font.Font(family="Helvetica", size=28, weight="bold")
            self.font_header = font.Font(family="Helvetica", size=20, weight="bold")
            self.font_subheader = font.Font(family="Helvetica", size=16, weight="bold")
            self.font_body = font.Font(family="Helvetica", size=14)
            self.font_small = font.Font(family="Helvetica", size=12)
            self.font_tiny = font.Font(family="Helvetica", size=10)
    
    def save_group_id(self, group_id):
        """Сохраняет ID группы в файл"""
        try:
            with open(self.config_file, 'w') as f:
                f.write(str(group_id))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить настройки: {e}")
    
    def load_group_id(self):
        """Загружает ID группы из файла"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return f.read().strip()
        except Exception:
            pass
        return None
    
    def get_monday_of_week(self, date):
        """Получает понедельник недели для заданной даты"""
        days_since_monday = date.weekday()
        monday = date - timedelta(days=days_since_monday)
        return monday
    
    def create_modern_interface(self):
        """Создает современный интерфейс в стиле Web UI"""
        # Хедер приложения
        self.create_header()
        
        # Основной контент
        self.create_main_content()
        
        # Футер/статус бар
        self.create_footer()
    
    def create_header(self):
        """Создает хедер в стиле современного веб-приложения"""
        header = tk.Frame(self.root, bg=self.colors['card_bg'], height=80)
        header.pack(fill='x', side='top')
        header.pack_propagate(False)
        
        # Контейнер с отступами
        header_content = tk.Frame(header, bg=self.colors['card_bg'])
        header_content.pack(fill='both', expand=True, padx=32, pady=16)
        
        # Левая часть - лого и название
        left_section = tk.Frame(header_content, bg=self.colors['card_bg'])
        left_section.pack(side='left', fill='y')
        
        # Иконка приложения (эмулируем Material Icons)
        icon_frame = tk.Frame(left_section, bg=self.colors['primary'], width=40, height=40)
        icon_frame.pack(side='left', pady=8)
        icon_frame.pack_propagate(False)
        
        icon_label = tk.Label(icon_frame, text="🎓", font=('SF Pro Display', 20), 
                             bg=self.colors['primary'], fg='white')
        icon_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Название приложения
        title_label = tk.Label(left_section, text="CampusConnect", 
                              font=self.font_subheader,
                              bg=self.colors['card_bg'], fg=self.colors['text_primary'])
        title_label.pack(side='left', padx=(16, 0), pady=8)
        
        # Правая часть - кнопки управления
        right_section = tk.Frame(header_content, bg=self.colors['card_bg'])
        right_section.pack(side='right', fill='y')
        
        # Кнопка настроек группы
        self.create_header_button(right_section, "⚙️", "Настройки", self.change_group)
        
        # Кнопка обновления
        self.create_header_button(right_section, "🔄", "Обновить", self.load_schedule)
        
        # Разделительная линия
        separator = tk.Frame(self.root, bg=self.colors['border'], height=1)
        separator.pack(fill='x')
    
    def create_header_button(self, parent, icon, tooltip, command):
        """Создает кнопку в хедере"""
        btn_frame = tk.Frame(parent, bg=self.colors['card_bg'], width=40, height=40)
        btn_frame.pack(side='right', padx=(0, 8))
        btn_frame.pack_propagate(False)
        
        btn = tk.Label(btn_frame, text=icon, font=('SF Pro Display', 16),
                      bg=self.colors['card_bg'], fg=self.colors['text_secondary'],
                      cursor='hand2')
        btn.place(relx=0.5, rely=0.5, anchor='center')
        btn.bind('<Button-1>', lambda e: command())
        btn.bind('<Enter>', lambda e: btn.config(fg=self.colors['primary']))
        btn.bind('<Leave>', lambda e: btn.config(fg=self.colors['text_secondary']))
    
    def create_main_content(self):
        """Создает основной контент"""
        main_frame = tk.Frame(self.root, bg=self.colors['bg_light'])
        main_frame.pack(fill='both', expand=True, padx=32, pady=24)
        
        # Заголовок страницы
        self.create_page_header(main_frame)
        
        # Табы (Daily/Weekly)
        self.create_tabs(main_frame)
        
        # Основная сетка контента
        content_grid = tk.Frame(main_frame, bg=self.colors['bg_light'])
        content_grid.pack(fill='both', expand=True, pady=(24, 0))
        
        # Левая колонка - календарь (1/3 ширины)
        self.calendar_frame = tk.Frame(content_grid, bg=self.colors['card_bg'], 
                                      relief='flat', bd=0, width=300)
        self.calendar_frame.pack(side='left', fill='y', padx=(0, 24))
        self.calendar_frame.pack_propagate(False)
        
        # Правая колонка - расписание (2/3 ширины)
        self.schedule_container = tk.Frame(content_grid, bg=self.colors['bg_light'])
        self.schedule_container.pack(side='right', fill='both', expand=True)
        
        # Создаем календарь и область расписания
        self.create_calendar()
        self.create_schedule_area()
    
    def create_page_header(self, parent):
        """Создает заголовок страницы"""
        header_section = tk.Frame(parent, bg=self.colors['bg_light'])
        header_section.pack(fill='x', pady=(0, 24))
        
        title = tk.Label(header_section, text="Мое расписание", 
                        font=self.font_title, 
                        bg=self.colors['bg_light'], fg=self.colors['primary'])
        title.pack(anchor='w')
        
        subtitle = tk.Label(header_section, text="Просмотр ежедневного или недельного расписания занятий", 
                           font=self.font_body, 
                           bg=self.colors['bg_light'], fg=self.colors['text_secondary'])
        subtitle.pack(anchor='w', pady=(4, 0))
    
    def create_tabs(self, parent):
        """Создает табы Daily/Weekly"""
        tabs_container = tk.Frame(parent, bg=self.colors['bg_light'])
        tabs_container.pack(fill='x', pady=(0, 24))
        
        # Линия под табами
        tabs_border = tk.Frame(tabs_container, bg=self.colors['border'], height=1)
        tabs_border.pack(fill='x', side='bottom')
        
        # Сами табы
        tabs_frame = tk.Frame(tabs_container, bg=self.colors['bg_light'])
        tabs_frame.pack(fill='x', side='top')
        
        # Таб Daily
        self.daily_tab = self.create_tab(tabs_frame, "На день", True, lambda: self.switch_view('daily'))
        
        # Таб Weekly  
        self.weekly_tab = self.create_tab(tabs_frame, "На неделю", False, lambda: self.switch_view('weekly'))
    
    def create_tab(self, parent, text, active, command):
        """Создает отдельный таб"""
        tab_frame = tk.Frame(parent, bg=self.colors['bg_light'])
        tab_frame.pack(side='left', padx=(0, 32))
        
        tab_btn = tk.Label(tab_frame, text=text, 
                          font=self.font_body if not active else font.Font(family="SF Pro Text", size=14, weight="bold"),
                          bg=self.colors['bg_light'], 
                          fg=self.colors['primary'] if active else self.colors['text_secondary'],
                          cursor='hand2', pady=12)
        tab_btn.pack()
        
        # Индикатор активного таба
        indicator_color = self.colors['primary'] if active else self.colors['bg_light']
        indicator = tk.Frame(tab_frame, bg=indicator_color, height=2)
        indicator.pack(fill='x')
        
        tab_btn.bind('<Button-1>', lambda e: command())
        
        return {'frame': tab_frame, 'btn': tab_btn, 'indicator': indicator}
    
    def switch_view(self, mode):
        """Переключает между режимами просмотра"""
        self.view_mode = mode
        
        # Обновляем табы
        if mode == 'daily':
            self.daily_tab['btn'].config(fg=self.colors['primary'], 
                                        font=font.Font(family="SF Pro Text", size=14, weight="bold"))
            self.daily_tab['indicator'].config(bg=self.colors['primary'])
            self.weekly_tab['btn'].config(fg=self.colors['text_secondary'], 
                                         font=self.font_body)
            self.weekly_tab['indicator'].config(bg=self.colors['bg_light'])
        else:
            self.weekly_tab['btn'].config(fg=self.colors['primary'], 
                                         font=font.Font(family="SF Pro Text", size=14, weight="bold"))
            self.weekly_tab['indicator'].config(bg=self.colors['primary'])
            self.daily_tab['btn'].config(fg=self.colors['text_secondary'], 
                                        font=self.font_body)
            self.daily_tab['indicator'].config(bg=self.colors['bg_light'])
        
        # Перезагружаем расписание
        self.load_schedule()
    
    def create_calendar(self):
        """Создает современный календарь"""
        # Заголовок календаря
        cal_header = tk.Frame(self.calendar_frame, bg=self.colors['card_bg'])
        cal_header.pack(fill='x', padx=16, pady=(16, 0))
        
        # Навигация по месяцам
        nav_frame = tk.Frame(cal_header, bg=self.colors['card_bg'])
        nav_frame.pack(fill='x', pady=(0, 16))
        
        # Кнопка назад
        prev_btn = tk.Label(nav_frame, text="‹", font=('SF Pro Display', 18),
                           bg=self.colors['card_bg'], fg=self.colors['text_secondary'],
                           cursor='hand2', width=3)
        prev_btn.pack(side='left')
        prev_btn.bind('<Button-1>', lambda e: self.change_month(-1))
        prev_btn.bind('<Enter>', lambda e: prev_btn.config(bg=self.colors['bg_light']))
        prev_btn.bind('<Leave>', lambda e: prev_btn.config(bg=self.colors['card_bg']))
        
        # Название месяца
        now = datetime.now()
        month_names = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                      'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
        
        self.month_label = tk.Label(nav_frame, 
                                   text=f"{month_names[now.month-1]} {now.year}",
                                   font=self.font_subheader,
                                   bg=self.colors['card_bg'], fg=self.colors['text_primary'])
        self.month_label.pack(side='left', expand=True)
        
        # Кнопка вперед
        next_btn = tk.Label(nav_frame, text="›", font=('SF Pro Display', 18),
                           bg=self.colors['card_bg'], fg=self.colors['text_secondary'],
                           cursor='hand2', width=3)
        next_btn.pack(side='right')
        next_btn.bind('<Button-1>', lambda e: self.change_month(1))
        next_btn.bind('<Enter>', lambda e: next_btn.config(bg=self.colors['bg_light']))
        next_btn.bind('<Leave>', lambda e: next_btn.config(bg=self.colors['card_bg']))
        
        # Навигационные кнопки недели
        week_nav = tk.Frame(cal_header, bg=self.colors['card_bg'])
        week_nav.pack(fill='x', pady=(8, 0))
        
        prev_week_btn = tk.Button(week_nav, text="← Пред. неделя", 
                                 command=self.prev_week,
                                 bg=self.colors['primary'], fg='white',
                                 font=self.font_tiny, relief='flat',
                                 cursor='hand2')
        prev_week_btn.pack(side='left', padx=(0, 4))
        
        current_week_btn = tk.Button(week_nav, text="Сегодня", 
                                    command=self.current_week,
                                    bg=self.colors['success'], fg='white',
                                    font=self.font_tiny, relief='flat',
                                    cursor='hand2')
        current_week_btn.pack(side='left', padx=2)
        
        next_week_btn = tk.Button(week_nav, text="След. неделя →", 
                                 command=self.next_week,
                                 bg=self.colors['primary'], fg='white',
                                 font=self.font_tiny, relief='flat',
                                 cursor='hand2')
        next_week_btn.pack(side='right', padx=(4, 0))
        
        # Сетка календаря
        self.create_calendar_grid()
    
    def create_calendar_grid(self):
        """Создает сетку календаря"""
        if hasattr(self, 'cal_grid'):
            self.cal_grid.destroy()
            
        self.cal_grid = tk.Frame(self.calendar_frame, bg=self.colors['card_bg'])
        self.cal_grid.pack(fill='both', expand=True, padx=16, pady=(0, 16))
        
        # Заголовки дней недели
        days = ['В', 'П', 'В', 'С', 'Ч', 'П', 'С']
        for i, day in enumerate(days):
            day_header = tk.Label(self.cal_grid, text=day, 
                                 font=font.Font(family="SF Pro Text", size=12, weight="bold"),
                                 bg=self.colors['card_bg'], fg=self.colors['text_secondary'])
            day_header.grid(row=0, column=i, pady=(0, 8), sticky='ew')
            self.cal_grid.columnconfigure(i, weight=1)
        
        # Генерируем дни месяца
        now = datetime.now()
        cal = calendar.monthcalendar(now.year, now.month)
        
        for week_num, week in enumerate(cal, 1):
            for day_num, day in enumerate(week):
                if day == 0:
                    continue
                    
                # Определяем, является ли день текущим
                is_today = (day == now.day and 
                           now.month == now.month and 
                           now.year == now.year)
                
                # Создаем кнопку дня
                day_btn = tk.Label(self.cal_grid, text=str(day),
                                  font=self.font_small,
                                  width=4, height=2,
                                  cursor='hand2')
                
                if is_today:
                    day_btn.config(bg=self.colors['primary'], fg='white',
                                  font=font.Font(family="SF Pro Text", size=12, weight="bold"))
                else:
                    day_btn.config(bg=self.colors['card_bg'], fg=self.colors['text_primary'])
                    day_btn.bind('<Enter>', lambda e, btn=day_btn: 
                                btn.config(bg=self.colors['bg_light']) if btn.cget('bg') != self.colors['primary'] else None)
                    day_btn.bind('<Leave>', lambda e, btn=day_btn: 
                                btn.config(bg=self.colors['card_bg']) if btn.cget('bg') != self.colors['primary'] else None)
                
                day_btn.grid(row=week_num, column=day_num, padx=1, pady=1, sticky='ew')
                day_btn.bind('<Button-1>', lambda e, d=day: self.select_date(d))
    
    def change_month(self, direction):
        """Изменяет месяц в календаре"""
        # TODO: Реализовать смену месяца
        pass
    
    def select_date(self, day):
        """Выбирает дату в календаре"""
        now = datetime.now()
        selected = datetime(now.year, now.month, day)
        self.selected_date = self.get_monday_of_week(selected)
        self.load_schedule()
    
    def prev_week(self):
        """Переход на предыдущую неделю"""
        self.selected_date -= timedelta(days=7)
        self.load_schedule()
    
    def next_week(self):
        """Переход на следующую неделю"""
        self.selected_date += timedelta(days=7)
        self.load_schedule()
    
    def current_week(self):
        """Переход на текущую неделю"""
        self.selected_date = self.current_date
        self.load_schedule()
    
    def create_schedule_area(self):
        """Создает область для отображения расписания"""
        # Заголовок расписания
        schedule_header = tk.Frame(self.schedule_container, bg=self.colors['bg_light'])
        schedule_header.pack(fill='x', pady=(0, 16))
        
        self.schedule_title = tk.Label(schedule_header, text="Занятия на сегодня", 
                                      font=self.font_header,
                                      bg=self.colors['bg_light'], fg=self.colors['text_primary'])
        self.schedule_title.pack(anchor='w')
        
        # Контейнер для карточек расписания
        self.schedule_scroll_frame = tk.Frame(self.schedule_container, bg=self.colors['bg_light'])
        self.schedule_scroll_frame.pack(fill='both', expand=True)
        
        # Создаем scrollable область
        canvas = tk.Canvas(self.schedule_scroll_frame, bg=self.colors['bg_light'], 
                          highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.schedule_scroll_frame, orient="vertical", command=canvas.yview)
        self.schedule_cards_frame = tk.Frame(canvas, bg=self.colors['bg_light'])
        
        self.schedule_cards_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.schedule_cards_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Привязываем прокрутку мышью
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
    
    def create_footer(self):
        """Создает футер со статусом"""
        footer = tk.Frame(self.root, bg=self.colors['text_primary'], height=40)
        footer.pack(fill='x', side='bottom')
        footer.pack_propagate(False)
        
        footer_content = tk.Frame(footer, bg=self.colors['text_primary'])
        footer_content.pack(fill='both', expand=True, padx=32, pady=8)
        
        self.status_label = tk.Label(footer_content, text="🟢 Готов к работе", 
                                    font=self.font_tiny,
                                    bg=self.colors['text_primary'], fg='#ecf0f1')
        self.status_label.pack(side='left')
        
        # Информация о группе в правом углу
        self.group_info_label = tk.Label(footer_content, text="", 
                                        font=self.font_tiny,
                                        bg=self.colors['text_primary'], fg='#ecf0f1')
        self.group_info_label.pack(side='right')
    
    def setup_group(self):
        """Первоначальная настройка группы"""
        group_id = simpledialog.askstring("Настройка группы", 
                                         "Введите ID вашей группы:",
                                         parent=self.root)
        if group_id:
            self.group_id = group_id.strip()
            self.save_group_id(self.group_id)
            self.update_group_info()
            self.load_schedule()
        else:
            self.root.quit()
    
    def change_group(self):
        """Смена группы"""
        current = self.group_id if self.group_id else ""
        group_id = simpledialog.askstring("Смена группы", 
                                         "Введите новый ID группы:",
                                         initialvalue=current,
                                         parent=self.root)
        if group_id:
            self.group_id = group_id.strip()
            self.save_group_id(self.group_id)
            self.update_group_info()
            self.load_schedule()
    
    def update_group_info(self):
        """Обновляет информацию о группе"""
        if self.group_id:
            self.group_info_label.config(text=f"Группа: {self.group_id}")
    
    def load_schedule(self):
        """Загружает расписание"""
        if not self.group_id:
            return
        
        # Обновляем статус
        self.status_label.config(text="⏳ Загрузка расписания...")
        
        # Очищаем область расписания
        for widget in self.schedule_cards_frame.winfo_children():
            widget.destroy()
        
        # Показываем индикатор загрузки
        self.show_loading()
        
        # Запускаем загрузку в отдельном потоке
        thread = threading.Thread(target=self._load_schedule_thread)
        thread.daemon = True
        thread.start()
    
    def show_loading(self):
        """Показывает индикатор загрузки"""
        loading_card = self.create_loading_card()
        loading_card.pack(fill='x', pady=(0, 16))
    
    def create_loading_card(self):
        """Создает карточку загрузки"""
        card = tk.Frame(self.schedule_cards_frame, bg=self.colors['card_bg'], 
                       relief='flat', bd=1, highlightbackground=self.colors['border'], 
                       highlightthickness=1)
        
        content = tk.Frame(card, bg=self.colors['card_bg'])
        content.pack(fill='both', expand=True, padx=24, pady=24)
        
        # Иконка загрузки
        icon_frame = tk.Frame(content, bg='#e3f2fd', width=48, height=48)
        icon_frame.pack(side='left', padx=(0, 16))
        icon_frame.pack_propagate(False)
        
        icon_label = tk.Label(icon_frame, text="⏳", font=('SF Pro Display', 20),
                             bg='#e3f2fd', fg=self.colors['primary'])
        icon_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Текст загрузки
        text_frame = tk.Frame(content, bg=self.colors['card_bg'])
        text_frame.pack(side='left', fill='both', expand=True)
        
        title_label = tk.Label(text_frame, text="Загрузка расписания...", 
                              font=self.font_subheader,
                              bg=self.colors['card_bg'], fg=self.colors['text_primary'])
        title_label.pack(anchor='w')
        
        subtitle_label = tk.Label(text_frame, text="Получение данных с сервера", 
                                 font=self.font_small,
                                 bg=self.colors['card_bg'], fg=self.colors['text_secondary'])
        subtitle_label.pack(anchor='w', pady=(4, 0))
        
        return card
    
    def _load_schedule_thread(self):
        """Загружает расписание из API"""
        try:
            date_str = self.selected_date.strftime('%Y-%m-%d')
            url = f"https://ruz.spbstu.ru/api/v1/ruz/scheduler/{self.group_id}?date={date_str}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Обновляем UI в главном потоке
            self.root.after(0, lambda: self._update_schedule_ui(data))
            
        except requests.RequestException as e:
            error_msg = f"Ошибка сети: {str(e)}"
            self.root.after(0, lambda: self._show_error(error_msg))
        except json.JSONDecodeError:
            self.root.after(0, lambda: self._show_error("Ошибка: Неверный формат данных"))
        except Exception as e:
            self.root.after(0, lambda: self._show_error(f"Неожиданная ошибка: {str(e)}"))
    
    def _update_schedule_ui(self, data):
        """Обновляет UI с полученными данными расписания"""
        # Очищаем текущее содержимое
        for widget in self.schedule_cards_frame.winfo_children():
            widget.destroy()
        
        if not data or 'week' not in data:
            self._show_error("Данные расписания не найдены")
            return
        
        # Обновляем заголовок
        if self.view_mode == 'daily':
            date_str = self.selected_date.strftime('%d.%m.%Y')
            day_name = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'][self.selected_date.weekday()]
            self.schedule_title.config(text=f"Занятия на {day_name}, {date_str}")
        else:
            start_date = self.selected_date
            end_date = start_date + timedelta(days=6)
            self.schedule_title.config(text=f"Занятия на неделю {start_date.strftime('%d.%m')} - {end_date.strftime('%d.%m.%Y')}")
        
        if self.view_mode == 'daily':
            self._show_daily_schedule(data)
        else:
            self._show_weekly_schedule(data)
        
        self.status_label.config(text="✅ Расписание загружено")
    
    def _show_daily_schedule(self, data):
        """Показывает расписание на день"""
        target_weekday = self.selected_date.weekday() + 1  # API использует 1-7
        
        day_data = None
        for day in data.get('days', []):
            if day.get('weekday') == target_weekday:
                day_data = day
                break
        
        if not day_data or not day_data.get('lessons'):
            self._show_no_classes()
            return
        
        # Сортируем уроки по времени
        lessons = sorted(day_data['lessons'], key=lambda x: x.get('time_start', ''))
        
        for idx, lesson in enumerate(lessons):
            is_current = self._is_current_lesson(lesson)
            card = self.create_class_card(lesson, is_current)
            card.pack(fill='x', pady=(0, 16))
    
    def _show_weekly_schedule(self, data):
        """Показывает расписание на неделю"""
        days_names = ["ВС", "ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ"]
        
        for wday in range(1, 8):
            day_data = None
            for day in data.get('days', []):
                if day.get('weekday') == wday:
                    day_data = day
                    break
            
            day_name = days_names[wday % 7]
            day_card = self.create_day_card(day_name, day_data)
            day_card.pack(fill='x', pady=(0, 16))
    
    def _show_no_classes(self):
        """Показывает сообщение об отсутствии занятий"""
        card = self.create_no_classes_card()
        card.pack(fill='x', pady=(0, 16))
    
    def _show_error(self, message):
        """Показывает ошибку"""
        for widget in self.schedule_cards_frame.winfo_children():
            widget.destroy()
        
        error_card = self.create_error_card(message)
        error_card.pack(fill='x', pady=(0, 16))
        
        self.status_label.config(text="❌ Ошибка загрузки")
    
    def create_class_card(self, lesson, is_current=False):
        """Создает карточку занятия в стиле Web UI"""
        card_color = '#fff7ed' if is_current else self.colors['card_bg']
        border_color = self.colors['current_class'] if is_current else self.colors['border']
        
        card = tk.Frame(self.schedule_cards_frame, bg=card_color, relief='flat', bd=1,
                       highlightbackground=border_color, highlightthickness=1)
        
        content = tk.Frame(card, bg=card_color)
        content.pack(fill='both', expand=True, padx=16, pady=16)
        
        # Иконка предмета
        subject_icons = {
            'математика': '📊', 'физика': '⚛️', 'химия': '🧪', 'информатика': '💻',
            'программирование': '💻', 'алгоритм': '🔢', 'база данных': '🗄️',
            'дизайн': '🎨', 'управление': '📈', 'маркетинг': '📈', 'логистика': '🚚'
        }
        
        subject_text = lesson.get('subject', '').lower()
        icon = '📚'  # по умолчанию
        for key, emoji in subject_icons.items():
            if key in subject_text:
                icon = emoji
                break
        
        icon_bg = '#ffedd5' if is_current else '#e3f2fd'
        icon_fg = self.colors['current_class'] if is_current else self.colors['primary']
        
        icon_frame = tk.Frame(content, bg=icon_bg, width=48, height=48)
        icon_frame.pack(side='left', padx=(0, 16))
        icon_frame.pack_propagate(False)
        
        icon_label = tk.Label(icon_frame, text=icon, font=('SF Pro Display', 20),
                             bg=icon_bg, fg=icon_fg)
        icon_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Информация о занятии
        info_frame = tk.Frame(content, bg=card_color)
        info_frame.pack(side='left', fill='both', expand=True)
        
        # Название предмета
        subject_label = tk.Label(info_frame, text=lesson.get('subject', 'Неизвестный предмет'), 
                                font=self.font_subheader,
                                bg=card_color, 
                                fg=self.colors['current_class'] if is_current else self.colors['text_primary'])
        subject_label.pack(anchor='w')
        
        # Время и статус
        time_start = lesson.get('time_start', '')
        time_end = lesson.get('time_end', '')
        time_text = f"{time_start} - {time_end}"
        
        if is_current:
            time_text += " (Сейчас)"
        
        time_label = tk.Label(info_frame, text=time_text, 
                             font=self.font_small,
                             bg=card_color, 
                             fg=self.colors['current_class'] if is_current else self.colors['text_secondary'])
        time_label.pack(anchor='w', pady=(4, 8))
        
        # Преподаватель и аудитория
        teachers = lesson.get('teachers', [])
        teacher_name = teachers[0].get('first_name', 'Неизвестно') if teachers else 'Неизвестно'
        
        auditories = lesson.get('auditories', [])
        if auditories:
            aud_name = auditories[0].get('name', 'Неизвестно')
            building = auditories[0].get('building', {}).get('name', 'Неизвестно')
            location = f"ауд. {aud_name}, {building}"
        else:
            location = "Аудитория не указана"
        
        details_text = f"👨‍🏫 {teacher_name} • 📍 {location}"
        details_label = tk.Label(info_frame, text=details_text, 
                                font=self.font_tiny,
                                bg=card_color, fg=self.colors['text_secondary'])
        details_label.pack(anchor='w')
        
        return card
    
    def create_day_card(self, day_name, day_data):
        """Создает карточку дня для недельного вида"""
        card = tk.Frame(self.schedule_cards_frame, bg=self.colors['card_bg'], 
                       relief='flat', bd=1, highlightbackground=self.colors['border'], 
                       highlightthickness=1)
        
        # Заголовок дня
        header = tk.Frame(card, bg=self.colors['primary'], height=40)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        day_label = tk.Label(header, text=day_name, font=self.font_subheader,
                            bg=self.colors['primary'], fg='white')
        day_label.pack(pady=8)
        
        # Содержимое
        content = tk.Frame(card, bg=self.colors['card_bg'])
        content.pack(fill='both', expand=True, padx=16, pady=16)
        
        if not day_data or not day_data.get('lessons'):
            no_classes = tk.Label(content, text="🏖️ Выходной день", 
                                 font=self.font_body,
                                 bg=self.colors['card_bg'], fg=self.colors['text_secondary'])
            no_classes.pack()
        else:
            lessons = sorted(day_data['lessons'], key=lambda x: x.get('time_start', ''))
            for lesson in lessons:
                lesson_text = f"• {lesson.get('time_start', '')} - {lesson.get('subject', 'Неизвестно')}"
                lesson_label = tk.Label(content, text=lesson_text, 
                                       font=self.font_small,
                                       bg=self.colors['card_bg'], fg=self.colors['text_primary'],
                                       anchor='w')
                lesson_label.pack(fill='x', pady=2)
        
        return card
    
    def create_no_classes_card(self):
        """Создает карточку для отсутствия занятий"""
        card = tk.Frame(self.schedule_cards_frame, bg=self.colors['card_bg'], 
                       relief='flat', bd=1, highlightbackground=self.colors['border'], 
                       highlightthickness=1)
        
        content = tk.Frame(card, bg=self.colors['card_bg'])
        content.pack(fill='both', expand=True, padx=24, pady=48)
        
        icon_label = tk.Label(content, text="🏖️", font=('SF Pro Display', 48),
                             bg=self.colors['card_bg'], fg=self.colors['text_secondary'])
        icon_label.pack()
        
        title_label = tk.Label(content, text="Нет занятий", 
                              font=self.font_header,
                              bg=self.colors['card_bg'], fg=self.colors['text_primary'])
        title_label.pack(pady=(16, 8))
        
        subtitle_label = tk.Label(content, text="На этот день занятий не запланировано", 
                                 font=self.font_body,
                                 bg=self.colors['card_bg'], fg=self.colors['text_secondary'])
        subtitle_label.pack()
        
        return card
    
    def create_error_card(self, message):
        """Создает карточку ошибки"""
        card = tk.Frame(self.schedule_cards_frame, bg='#fef2f2', 
                       relief='flat', bd=1, highlightbackground='#fecaca', 
                       highlightthickness=1)
        
        content = tk.Frame(card, bg='#fef2f2')
        content.pack(fill='both', expand=True, padx=24, pady=24)
        
        icon_label = tk.Label(content, text="❌", font=('SF Pro Display', 32),
                             bg='#fef2f2', fg=self.colors['error'])
        icon_label.pack()
        
        title_label = tk.Label(content, text="Ошибка загрузки", 
                              font=self.font_subheader,
                              bg='#fef2f2', fg=self.colors['error'])
        title_label.pack(pady=(16, 8))
        
        message_label = tk.Label(content, text=message, 
                                font=self.font_small,
                                bg='#fef2f2', fg='#991b1b',
                                wraplength=400)
        message_label.pack()
        
        return card
    
    def _is_current_lesson(self, lesson):
        """Проверяет, является ли урок текущим"""
        now = datetime.now()
        today = now.date()
        selected_date = self.selected_date.date()
        
        # Проверяем только если выбранная дата - сегодня
        if selected_date != today:
            return False
        
        try:
            time_start = datetime.strptime(lesson.get('time_start', ''), '%H:%M').time()
            time_end = datetime.strptime(lesson.get('time_end', ''), '%H:%M').time()
            current_time = now.time()
            
            return time_start <= current_time <= time_end
        except:
            return False

def main():
    """Главная функция"""
    root = tk.Tk()
    app = ModernScheduleApp(root)
    
    # Центрируем окно
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()