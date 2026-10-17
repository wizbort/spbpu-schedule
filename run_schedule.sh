#!/bin/bash

# Лаунчер для приложения расписания
cd "$(dirname "$0")"

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    osascript -e 'display dialog "Python 3 не найден! Установите Python с https://python.org" buttons {"OK"} default button "OK"'
    exit 1
fi

# Проверяем библиотеки
if ! python3 -c "import tkinter, requests" 2>/dev/null; then
    osascript -e 'display dialog "Устанавливаю необходимые библиотеки..." buttons {"OK"} default button "OK"'
    pip3 install requests
fi

# Запускаем приложение
python3 schedule_app.py