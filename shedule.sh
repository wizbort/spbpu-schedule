#!/bin/bash

# Файл конфигурации
CONFIG_FILE="/path/to/Desktop/Программирование/Скрипты/Расписание СПбПУ/.schedule_config"

# Функция для сохранения ID группы
save_group_id() {
    echo "$1" > "$CONFIG_FILE"
}

# Функция для загрузки ID группы
load_group_id() {
    if [ -f "$CONFIG_FILE" ]; then
        cat "$CONFIG_FILE"
    else
        echo ""
    fi
}

# Функция для получения понедельника текущей недели
get_monday_of_week() {
    local date="$1"
    # Получаем день недели (1=понедельник, 7=воскресенье)
    local dow=$(date -j -f "%Y-%m-%d" "$date" "+%u" 2>/dev/null || date -d "$date" "+%u" 2>/dev/null)
    # Вычисляем количество дней до понедельника
    local days_to_monday=$((dow - 1))
    # Получаем дату понедельника
    if command -v gdate >/dev/null 2>&1; then
        # macOS с GNU date
        gdate -d "$date - $days_to_monday days" "+%Y-%m-%d"
    elif date -j >/dev/null 2>&1; then
        # macOS с BSD date
        date -j -v-${days_to_monday}d -f "%Y-%m-%d" "$date" "+%Y-%m-%d"
    else
        # Linux
        date -d "$date - $days_to_monday days" "+%Y-%m-%d"
    fi
}

# Функция для добавления/вычитания дней к дате
add_days() {
    local date="$1"
    local days="$2"
    
    if command -v gdate >/dev/null 2>&1; then
        # macOS с GNU date
        gdate -d "$date + $days days" "+%Y-%m-%d"
    elif date -j >/dev/null 2>&1; then
        # macOS с BSD date
        if [ "$days" -ge 0 ]; then
            date -j -v+${days}d -f "%Y-%m-%d" "$date" "+%Y-%m-%d"
        else
            local abs_days=$((-days))
            date -j -v-${abs_days}d -f "%Y-%m-%d" "$date" "+%Y-%m-%d"
        fi
    else
        # Linux
        date -d "$date + $days days" "+%Y-%m-%d"
    fi
}

# Функция для отображения расписания
show_schedule() {
    local group_id="$1"
    local date="$2"
    
    echo "📅 Загружаю расписание..."
    echo ""
    
    # Получаем данные из API
    DATA=$(curl -s "https://ruz.spbstu.ru/api/v1/ruz/scheduler/$group_id?date=$date")
    
    # Проверяем, получили ли данные
    if [ -z "$DATA" ] || [ "$DATA" = "null" ]; then
        echo "❌ Ошибка: Не удалось получить данные расписания"
        return 1
    fi
    
    # Извлекаем даты недели
    DATE_START=$(echo "$DATA" | jq -r '.week.date_start')
    DATE_END=$(echo "$DATA" | jq -r '.week.date_end')
    
    if [ "$DATE_START" = "null" ] || [ "$DATE_END" = "null" ]; then
        echo "❌ Ошибка: Неверный ID группы или дата"
        return 1
    fi
    
    echo "📚 Расписание группы $group_id"
    echo "📆 Неделя с $DATE_START по $DATE_END"
    echo ""
    
    # Массив названий дней недели
    DAYS=("ВС" "ПН" "ВТ" "СР" "ЧТ" "ПТ" "СБ")
    
    # Проходим по всем дням недели
    for WDAY in {1..7}; do
        DAY=$(echo "$DATA" | jq --argjson w $WDAY '.days[] | select(.weekday==$w)')
        DAY_NAME=${DAYS[$((WDAY%7))]}
        
        if [ -z "$DAY" ]; then
            echo "$DAY_NAME — Выходной"
            echo ""
            continue
        fi
        
        # Проходим по всем урокам дня
        echo "$DAY_NAME"
        LESSONS=$(echo "$DAY" | jq -c '.lessons[]')
        IDX=1
        while IFS= read -r LESSON; do
            SUBJECT=$(echo "$LESSON" | jq -r '.subject')
            TEACHER=$(echo "$LESSON" | jq -r '.teachers[0].first_name')
            TIME_START=$(echo "$LESSON" | jq -r '.time_start')
            TIME_END=$(echo "$LESSON" | jq -r '.time_end')
            AUD=$(echo "$LESSON" | jq -r '.auditories[0].name')
            BUILDING=$(echo "$LESSON" | jq -r '.auditories[0].building.name')
            
            echo "$IDX. $SUBJECT — $TEACHER"
            echo "🕒 $TIME_START - $TIME_END — ауд. $AUD, $BUILDING"
            IDX=$((IDX+1))
        done <<< "$LESSONS"
        
        echo ""
    done
}

# Функция главного меню
show_menu() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📋 РАСПИСАНИЕ СПбПУ"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "1) Показать текущую неделю"
    echo "2) ⬅️  Предыдущая неделя"
    echo "3) ➡️  Следующая неделя"
    echo "4) 📅 Выбрать дату"
    echo "5) ⚙️  Сменить группу"
    echo "6) ❌ Выход"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Основная программа
main() {
    # Загружаем ID группы
    GROUP_ID=$(load_group_id)
    
    # Если ID группы не сохранён, просим ввести
    if [ -z "$GROUP_ID" ]; then
        echo "🎓 Добро пожаловать в программу просмотра расписания СПбПУ!"
        echo ""
        echo -n "Введите ID вашей группы: "
        read GROUP_ID
        if [ -z "$GROUP_ID" ]; then
            echo "❌ ID группы не может быть пустым"
            exit 1
        fi
        save_group_id "$GROUP_ID"
        echo "✅ ID группы $GROUP_ID сохранён"
        echo ""
    fi
    
    # Текущая дата (понедельник текущей недели)
    CURRENT_DATE=$(get_monday_of_week $(date "+%Y-%m-%d"))
    SELECTED_DATE="$CURRENT_DATE"
    
    while true; do
        clear
        show_schedule "$GROUP_ID" "$SELECTED_DATE"
        show_menu
        
        echo -n "Выберите действие: "
        read choice
        
        case $choice in
            1)
                SELECTED_DATE="$CURRENT_DATE"
                ;;
            2)
                SELECTED_DATE=$(add_days "$SELECTED_DATE" -7)
                ;;
            3)
                SELECTED_DATE=$(add_days "$SELECTED_DATE" 7)
                ;;
            4)
                echo -n "Введите дату (YYYY-MM-DD): "
                read input_date
                if date -j -f "%Y-%m-%d" "$input_date" >/dev/null 2>&1 || date -d "$input_date" >/dev/null 2>&1; then
                    SELECTED_DATE=$(get_monday_of_week "$input_date")
                else
                    echo "❌ Неверный формат даты. Нажмите Enter для продолжения..."
                    read
                fi
                ;;
            5)
                echo -n "Введите новый ID группы: "
                read new_group_id
                if [ -n "$new_group_id" ]; then
                    GROUP_ID="$new_group_id"
                    save_group_id "$GROUP_ID"
                    echo "✅ ID группы изменён на $GROUP_ID"
                    echo "Нажмите Enter для продолжения..."
                    read
                fi
                ;;
            6)
                echo "👋 До свидания!"
                exit 0
                ;;
            *)
                echo "❌ Неверный выбор. Нажмите Enter для продолжения..."
                read
                ;;
        esac
    done
}

# Запускаем основную программу
main