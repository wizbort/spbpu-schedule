// ============== НАСТРОЙКИ ==============
// Группа настраивается автоматически через диалоговое окно при первом запуске
// Для смены группы - нажмите на виджет в приложении Scriptable, и нажмите сменить группу
// ID группы и факультета (заполняются автоматически)
let GROUP_ID = null;
let FACULTY_ID = null;
let GROUP_NAME = null;

// Файл для хранения настроек группы
const CONFIG_FILE = "spbpu_group_config.json";

// URL для открытия расписания (обновляется после загрузки конфига)
let SCHEDULE_URL = "https://ruz.spbstu.ru/";

// Цветовая схема
const COLORS = {
  primary: new Color("#5EB157"),
  background: Color.dynamic(new Color("#ffffff"), new Color("#1c1c1e")),
  cardBackground: Color.dynamic(new Color("#ffffff"), new Color("#2c2c2e")),
  textPrimary: Color.dynamic(new Color("#101922"), new Color("#ffffff")),
  textSecondary: Color.dynamic(new Color("#6b7280"), new Color("#98989d")),
  currentClass: new Color("#f97316"),
  noClasses: new Color("#5EB157"),
  error: new Color("#ef4444"),
};

// ============== ОСНОВНОЙ КОД ==============

// Кэш для данных
const CACHE_DURATION = 1 * 10 * 10 * 1000; // 1 час в миллисекундах

// Показать диалог для ввода номера группы
async function showGroupInputDialog(prefill = "") {
  const alert = new Alert();
  alert.title = "Настройка расписания";
  alert.message = "Введите номер вашей группы\nПример: 3733805/20201";
  alert.addTextField("Номер группы", prefill);
  alert.addAction("Найти группу");
  alert.addCancelAction("Отмена");

  const result = await alert.present();

  if (result === -1) {
    // Нажата отмена
    return null;
  }

  return alert.textFieldValue(0).trim();
}

// Показать диалог выбора группы из найденных
async function showGroupSelectionDialog(groups) {
  const alert = new Alert();
  alert.title = "Выберите группу";
  alert.message = `Найдено ${groups.length} групп(ы)`;

  for (const group of groups.slice(0, 5)) {
    alert.addAction(`${group.name}\n${group.faculty.abbr}`);
  }
  alert.addCancelAction("Отмена");

  const result = await alert.present();

  if (result === -1) {
    return null;
  }

  return groups[result];
}

// Показать сообщение об успехе
async function showSuccessDialog(groupName, facultyName) {
  const alert = new Alert();
  alert.title = "Группа настроена!";
  alert.message = `Группа: ${groupName}\nФакультет: ${facultyName}\n\nТеперь добавьте виджет на рабочий стол.`;
  alert.addAction("OK");
  await alert.present();
}

// Показать сообщение об ошибке
async function showErrorDialog(message) {
  const alert = new Alert();
  alert.title = "Ошибка";
  alert.message = message;
  alert.addAction("OK");
  await alert.present();
}

// Поиск группы через API
async function searchGroup(groupName) {
  try {
    // encodeURIComponent кодирует / как %2F, но API ожидает обычный /
    const encodedName = encodeURIComponent(groupName).replace(/%2F/g, "/");
    const searchUrl = `https://ruz.spbstu.ru/api/v1/ruz/search/groups?q=${encodedName}`;
    console.log(`Поиск группы: ${searchUrl}`);

    const request = new Request(searchUrl);
    request.timeoutInterval = 15;
    const response = await request.loadString();
    console.log(`Ответ API: ${response.substring(0, 200)}...`);

    const data = JSON.parse(response);
    const groups = data.groups || [];
    console.log(`Найдено групп: ${groups.length}`);

    if (groups.length === 0) {
      await showErrorDialog(
        `Группа "${groupName}" не найдена.\nПроверьте правильность номера.`,
      );
    }

    return groups;
  } catch (e) {
    console.error("Ошибка поиска группы:", e.message || e);
    // Показываем ошибку пользователю
    await showErrorDialog(
      `Ошибка подключения к серверу расписания:\n${e.message || e}`,
    );
    return [];
  }
}

// Сохранить конфигурацию группы
function saveGroupConfig(group) {
  const fm = FileManager.local();
  const configPath = fm.joinPath(fm.documentsDirectory(), CONFIG_FILE);

  const config = {
    groupName: group.name,
    groupId: String(group.id),
    facultyId: String(group.faculty.id),
    faculty: group.faculty.name,
    facultyAbbr: group.faculty.abbr,
    spec: group.spec,
    timestamp: Date.now(),
  };

  fm.writeString(configPath, JSON.stringify(config));

  GROUP_NAME = config.groupName;
  GROUP_ID = config.groupId;
  FACULTY_ID = config.facultyId;
  SCHEDULE_URL = `https://ruz.spbstu.ru/faculty/${FACULTY_ID}/groups/${GROUP_ID}`;

  console.log(`Конфиг сохранён: ${config.groupName} (ID: ${config.groupId})`);
}

// Загрузка конфигурации группы
async function loadGroupConfig() {
  const fm = FileManager.local();
  const configPath = fm.joinPath(fm.documentsDirectory(), CONFIG_FILE);

  // Пробуем загрузить сохранённый конфиг
  try {
    if (fm.fileExists(configPath)) {
      const savedConfig = JSON.parse(fm.readString(configPath));
      if (
        savedConfig.groupId &&
        savedConfig.facultyId &&
        savedConfig.groupName
      ) {
        GROUP_NAME = savedConfig.groupName;
        GROUP_ID = savedConfig.groupId;
        FACULTY_ID = savedConfig.facultyId;
        SCHEDULE_URL = `https://ruz.spbstu.ru/faculty/${FACULTY_ID}/groups/${GROUP_ID}`;
        console.log(`Конфиг загружен: ${GROUP_NAME} (ID: ${GROUP_ID})`);
        return true;
      }
    }
  } catch (e) {
    console.error("Ошибка чтения конфига:", e);
  }

  // Если запущен как виджет - нельзя показывать диалоги
  if (config.runsInWidget) {
    console.log("Виджет запущен без конфига");
    return false;
  }

  // Показываем диалог для ввода группы
  const inputGroupName = await showGroupInputDialog();

  if (!inputGroupName) {
    return false;
  }

  // Ищем группу
  const groups = await searchGroup(inputGroupName);

  if (groups.length === 0) {
    // Если searchGroup уже показал ошибку сети, не показываем ещё одну
    // groups будет пустым и при ошибке сети, и при отсутствии группы
    // но ошибка сети уже показана в searchGroup
    return false;
  }

  let selectedGroup;

  if (groups.length === 1) {
    // Если найдена одна группа - используем её
    selectedGroup = groups[0];
  } else {
    // Если несколько - даём выбрать
    // Сначала ищем точное совпадение
    const exactMatch = groups.find((g) => g.name === inputGroupName);
    if (exactMatch) {
      selectedGroup = exactMatch;
    } else {
      selectedGroup = await showGroupSelectionDialog(groups);
      if (!selectedGroup) {
        return false;
      }
    }
  }

  // Сохраняем выбранную группу
  saveGroupConfig(selectedGroup);

  // Показываем сообщение об успехе
  await showSuccessDialog(selectedGroup.name, selectedGroup.faculty.name);

  return true;
}

// Очистить кэш расписания
function clearScheduleCache() {
  const fm = FileManager.local();
  const cacheDir = fm.cacheDirectory();

  try {
    const files = fm.listContents(cacheDir);
    for (const file of files) {
      if (file.startsWith("schedule_") && file.endsWith(".json")) {
        const filePath = fm.joinPath(cacheDir, file);
        fm.remove(filePath);
        console.log(`Удалён кэш: ${file}`);
      }
    }
  } catch (e) {
    console.error("Ошибка очистки кэша:", e);
  }
}

// Сброс настроек (для смены группы)
async function resetConfig() {
  const fm = FileManager.local();
  const configPath = fm.joinPath(fm.documentsDirectory(), CONFIG_FILE);

  // Удаляем файл конфига
  if (fm.fileExists(configPath)) {
    fm.remove(configPath);
  }

  // Очищаем кэш расписания старой группы
  clearScheduleCache();

  GROUP_ID = null;
  FACULTY_ID = null;
  GROUP_NAME = null;

  console.log("Конфиг и кэш очищены");
}

class ScheduleWidget {
  constructor() {
    this.fm = FileManager.local();
    this.cacheDir = this.fm.cacheDirectory();
  }

  // Получить понедельник недели для даты
  getMondayOfWeek(date) {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1);
    d.setDate(diff);
    d.setHours(0, 0, 0, 0);
    return d;
  }

  // Форматирование даты для API
  formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  // Загрузка расписания для конкретной недели из API
  async fetchScheduleForWeek(monday) {
    const dateStr = this.formatDate(monday);
    // Добавляем GROUP_ID в имя файла кэша, чтобы разные группы не конфликтовали
    const cacheKey = `schedule_${GROUP_ID}_${dateStr}`;
    const cachePath = this.fm.joinPath(this.cacheDir, cacheKey + ".json");

    // Пробуем загрузить из кэша
    try {
      if (this.fm.fileExists(cachePath)) {
        const cacheData = JSON.parse(this.fm.readString(cachePath));
        const now = Date.now();
        if (cacheData.timestamp && now - cacheData.timestamp < CACHE_DURATION) {
          console.log(`Данные за ${dateStr} загружены из кэша`);
          return cacheData.data;
        }
      }
    } catch (e) {
      console.error("Ошибка чтения кэша:", e);
    }

    // Загружаем из API
    const url = `https://ruz.spbstu.ru/api/v1/ruz/scheduler/${GROUP_ID}?date=${dateStr}`;

    try {
      const request = new Request(url);
      request.timeoutInterval = 15;
      const data = await request.loadJSON();

      // Сохраняем в кэш
      try {
        const cacheData = { timestamp: Date.now(), data: data };
        this.fm.writeString(cachePath, JSON.stringify(cacheData));
      } catch (e) {}

      return data;
    } catch (e) {
      console.error("Ошибка загрузки расписания:", e);

      // Пробуем вернуть устаревший кэш
      try {
        if (this.fm.fileExists(cachePath)) {
          const cacheData = JSON.parse(this.fm.readString(cachePath));
          return cacheData.data;
        }
      } catch (e2) {}

      return null;
    }
  }

  // Загрузка расписания (текущая + следующая неделя)
  async fetchSchedule() {
    const now = new Date();
    const currentMonday = this.getMondayOfWeek(now);
    const nextMonday = new Date(currentMonday);
    nextMonday.setDate(currentMonday.getDate() + 7);

    const [currentWeek, nextWeek] = await Promise.all([
      this.fetchScheduleForWeek(currentMonday),
      this.fetchScheduleForWeek(nextMonday),
    ]);

    return {
      currentWeek: currentWeek,
      nextWeek: nextWeek,
      currentMonday: currentMonday,
      nextMonday: nextMonday,
    };
  }

  // Получить занятия на сегодня
  getTodayLessons(data) {
    if (!data || !data.currentWeek) return [];

    const now = new Date();
    const weekday = now.getDay() === 0 ? 7 : now.getDay();

    return this.getLessonsForWeekday(data.currentWeek, weekday);
  }

  // Проверить, является ли урок текущим
  isCurrentLesson(lesson) {
    const now = new Date();
    const currentTime = now.getHours() * 60 + now.getMinutes();

    try {
      const [startH, startM] = lesson.time_start.split(":").map(Number);
      const [endH, endM] = lesson.time_end.split(":").map(Number);
      const startTime = startH * 60 + startM;
      const endTime = endH * 60 + endM;

      return currentTime >= startTime && currentTime <= endTime;
    } catch (e) {
      return false;
    }
  }

  // Получить следующий урок
  getNextLesson(lessons) {
    const now = new Date();
    const currentTime = now.getHours() * 60 + now.getMinutes();

    for (const lesson of lessons) {
      try {
        const [startH, startM] = lesson.time_start.split(":").map(Number);
        const startTime = startH * 60 + startM;

        if (startTime > currentTime) {
          return lesson;
        }
      } catch (e) {
        continue;
      }
    }

    return null;
  }

  // Получить название дня недели
  getDayName(date = new Date()) {
    const days = [
      "Воскресенье",
      "Понедельник",
      "Вторник",
      "Среда",
      "Четверг",
      "Пятница",
      "Суббота",
    ];
    return days[date.getDay()];
  }

  // Форматирование даты для отображения (10 февраля)
  getFormattedDate(date = new Date()) {
    const months = [
      "января",
      "февраля",
      "марта",
      "апреля",
      "мая",
      "июня",
      "июля",
      "августа",
      "сентября",
      "октября",
      "ноября",
      "декабря",
    ];
    const day = date.getDate();
    const month = months[date.getMonth()];
    return `${day} ${month}`;
  }

  // Полная дата: "Вторник, 10 февраля"
  getFullDate(date = new Date()) {
    return `${this.getDayName(date)}, ${this.getFormattedDate(date)}`;
  }

  // Сокращение текста если слишком длинный
  truncate(str, maxLength) {
    if (!str) return "";
    if (str.length <= maxLength) return str;
    return str.substring(0, maxLength - 2) + "...";
  }

  // Склонение слова "пара"
  getLessonWord(count) {
    const lastDigit = count % 10;
    const lastTwoDigits = count % 100;

    if (lastTwoDigits >= 11 && lastTwoDigits <= 19) return "пар";
    if (lastDigit === 1) return "пара";
    if (lastDigit >= 2 && lastDigit <= 4) return "пары";
    return "пар";
  }

  // Получить ФИО преподавателя
  getTeacherName(lesson) {
    if (lesson.teachers && lesson.teachers.length > 0) {
      return lesson.teachers[0].full_name || "Не указан";
    }
    return "Не указан";
  }

  // Получить короткое ФИО (Фамилия И.О.)
  getShortTeacherName(lesson) {
    if (lesson.teachers && lesson.teachers.length > 0) {
      const t = lesson.teachers[0];
      // В API: first_name = фамилия, middle_name = имя, last_name = отчество
      const surname = t.first_name || "";
      const name = t.middle_name || "";
      const patronymic = t.last_name || "";
      if (surname && name) {
        return `${surname} ${name.charAt(0)}.${patronymic ? patronymic.charAt(0) + "." : ""}`;
      }
      return t.full_name || "Не указан";
    }
    return "Не указан";
  }

  // Получить тип занятия (Лекция, Практика и т.д.)
  getLessonType(lesson) {
    if (lesson.typeObj && lesson.typeObj.name) {
      // Сокращаем некоторые названия
      const name = lesson.typeObj.name;
      if (name === "Лекции") return "Лекция";
      if (name === "Практика") return "Практика";
      if (name === "Лабораторные") return "Лаб. работа";
      if (name === "Курсовое проектирование") return "Курс. проект";
      if (name === "Консультация") return "Консультация";
      if (name === "Экзамен") return "Экзамен";
      if (name === "Зачет") return "Зачёт";
      if (name === "Зачёт") return "Зачёт";
      if (name.includes("Доп")) return "Доп. сессия";
      if (name.includes("Переэкз")) return "Переэкз.";
      return name;
    }
    // Fallback на abbr
    if (lesson.typeObj && lesson.typeObj.abbr) {
      return lesson.typeObj.abbr;
    }
    return "";
  }

  // Форматирование аудитории: "1245 - 50 кор." или "Дистанционно"
  formatAuditory(lesson) {
    if (lesson.auditories && lesson.auditories.length > 0) {
      const aud = lesson.auditories[0];
      const audName = aud.name || "";

      // Проверяем на дистанционку
      if (
        audName.toLowerCase().includes("дистанц") ||
        (aud.building && aud.building.abbr === "DL")
      ) {
        return "Дистанционно";
      }

      if (aud.building) {
        // Извлекаем номер корпуса из abbr (например "50 уч.к" -> "50")
        const abbr = aud.building.abbr || "";
        const buildingNum = abbr.split(" ")[0] || abbr;
        return `${audName} - ${buildingNum} кор.`;
      }
      return audName;
    }
    return "Не указана";
  }

  // Форматирование аудитории с типом занятия: "1245 - 50 кор. - Лекция"
  formatAuditoryWithType(lesson) {
    const auditory = this.formatAuditory(lesson);
    const lessonType = this.getLessonType(lesson);
    if (lessonType) {
      return `${auditory} - ${lessonType}`;
    }
    return auditory;
  }

  // Получить все дни недели с датами
  getWeekDays() {
    const monday = this.getMondayOfWeek(new Date());
    const days = [];
    const dayNames = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

    for (let i = 0; i < 7; i++) {
      const date = new Date(monday);
      date.setDate(monday.getDate() + i);
      days.push({
        weekday: i + 1, // 1-7
        date: date,
        name: dayNames[i],
        formatted: `${String(date.getDate()).padStart(2, "0")}.${String(date.getMonth() + 1).padStart(2, "0")}`,
      });
    }
    return days;
  }

  // Получить занятия на конкретный день недели из данных недели
  getLessonsForWeekday(weekData, weekday) {
    if (!weekData || !weekData.days) return [];

    for (const day of weekData.days) {
      if (day.weekday === weekday) {
        const lessons = day.lessons || [];
        return lessons.sort((a, b) => {
          return (a.time_start || "").localeCompare(b.time_start || "");
        });
      }
    }
    return [];
  }

  // Получить ближайшие пары (на несколько дней вперёд, включая следующую неделю)
  // showFreeDays - показывать ли выходные дни
  getUpcomingLessons(data, maxLessons = 5, showFreeDays = false) {
    const result = [];
    const now = new Date();
    const currentTime = now.getHours() * 60 + now.getMinutes();

    // Проходим по дням начиная с сегодня (до 14 дней вперёд - 2 недели)
    for (
      let dayOffset = 0;
      dayOffset < 14 && result.length < maxLessons;
      dayOffset++
    ) {
      const targetDate = new Date(now);
      targetDate.setDate(now.getDate() + dayOffset);
      targetDate.setHours(0, 0, 0, 0);

      // Определяем день недели (1-7, где 1 = ПН)
      const weekday = targetDate.getDay() === 0 ? 7 : targetDate.getDay();

      // Определяем, это текущая или следующая неделя
      const targetMonday = this.getMondayOfWeek(targetDate);
      let weekData;

      if (
        data.currentMonday &&
        targetMonday.getTime() === data.currentMonday.getTime()
      ) {
        weekData = data.currentWeek;
      } else if (
        data.nextMonday &&
        targetMonday.getTime() === data.nextMonday.getTime()
      ) {
        weekData = data.nextWeek;
      } else {
        continue;
      }

      const lessons = this.getLessonsForWeekday(weekData, weekday);

      // Если нет пар и нужно показывать выходные
      if (lessons.length === 0 && showFreeDays) {
        result.push({
          lesson: null,
          date: new Date(targetDate),
          weekday: weekday,
          isFreeDay: true,
        });
        continue;
      }

      for (const lesson of lessons) {
        if (result.length >= maxLessons) break;

        // Для сегодня пропускаем прошедшие пары
        if (dayOffset === 0) {
          try {
            const [endH, endM] = lesson.time_end.split(":").map(Number);
            const endTime = endH * 60 + endM;
            if (endTime < currentTime) continue;
          } catch (e) {}
        }

        result.push({
          lesson: lesson,
          date: new Date(targetDate),
          weekday: weekday,
          isFreeDay: false,
        });
      }
    }

    return result;
  }

  // Получить полное ФИО преподавателя
  getFullTeacherName(lesson) {
    if (lesson.teachers && lesson.teachers.length > 0) {
      const t = lesson.teachers[0];
      // В API: first_name = фамилия, middle_name = имя, last_name = отчество
      const surname = t.first_name || "";
      const name = t.middle_name || "";
      const patronymic = t.last_name || "";
      if (surname) {
        return `${surname} ${name} ${patronymic}`.trim();
      }
      return t.full_name || "Не указан";
    }
    return "Не указан";
  }

  // ============== СОЗДАНИЕ ВИДЖЕТОВ ==============

  // Маленький виджет - показывает следующую пару
  async createSmallWidget() {
    const widget = new ListWidget();
    widget.backgroundColor = COLORS.background;
    widget.setPadding(12, 14, 12, 14);
    widget.url = SCHEDULE_URL;

    const data = await this.fetchSchedule();
    const upcoming = this.getUpcomingLessons(data, 1, true);

    // Заголовок
    const titleText = widget.addText("📚 Следующая пара");
    titleText.font = Font.boldSystemFont(13);
    titleText.textColor = COLORS.primary;

    widget.addSpacer(6);

    if (upcoming.length === 0) {
      widget.addSpacer();
      const noClassText = widget.addText("Нет занятий");
      noClassText.font = Font.systemFont(13);
      noClassText.textColor = COLORS.noClasses;
      widget.addSpacer();
    } else {
      const item = upcoming[0];

      // Дата
      const dateText = widget.addText(this.getFullDate(item.date));
      dateText.font = Font.systemFont(11);
      dateText.textColor = COLORS.textSecondary;

      widget.addSpacer(4);

      // Если выходной
      if (item.isFreeDay) {
        widget.addSpacer();
        const freeText = widget.addText("Выходной");
        freeText.font = Font.systemFont(13);
        freeText.textColor = COLORS.noClasses;
        widget.addSpacer();
      } else {
        const lesson = item.lesson;

        // Время
        const timeText = widget.addText(
          `${lesson.time_start} - ${lesson.time_end}`,
        );
        timeText.font = Font.systemFont(13);
        timeText.textColor = COLORS.textPrimary;

        // Название предмета
        const subjectText = widget.addText(lesson.subject || "Предмет");
        subjectText.font = Font.boldSystemFont(13);
        subjectText.textColor = COLORS.textPrimary;
        subjectText.minimumScaleFactor = 0.7;

        // Аудитория с типом занятия
        const audText = widget.addText(this.formatAuditoryWithType(lesson));
        audText.font = Font.systemFont(13);
        audText.textColor = COLORS.textSecondary;

        // Преподаватель
        const teacherText = widget.addText(this.getShortTeacherName(lesson));
        teacherText.font = Font.systemFont(13);
        teacherText.textColor = COLORS.textSecondary;
      }
    }

    widget.refreshAfterDate = new Date(Date.now() + CACHE_DURATION);

    return widget;
  }

  // Средний виджет - показывает ближайшие пары
  async createMediumWidget() {
    const widget = new ListWidget();
    widget.backgroundColor = COLORS.background;
    widget.setPadding(10, 14, 10, 14);
    widget.url = SCHEDULE_URL;

    const data = await this.fetchSchedule();
    const upcoming = this.getUpcomingLessons(data, 5, true);

    // Заголовок
    const titleText = widget.addText("📚 Ближайшие пары");
    titleText.font = Font.boldSystemFont(13);
    titleText.textColor = COLORS.primary;

    widget.addSpacer(6);

    if (upcoming.length === 0) {
      widget.addSpacer();
      const noClassText = widget.addText("Нет занятий");
      noClassText.font = Font.systemFont(13);
      noClassText.textColor = COLORS.noClasses;
      widget.addSpacer();
    } else {
      let currentDate = null;
      let itemsShown = 0;
      const maxItemsToShow = 3;

      for (let i = 0; i < upcoming.length && itemsShown < maxItemsToShow; i++) {
        const item = upcoming[i];
        const dateKey = item.date.toDateString();

        // Новый день - показываем заголовок дня
        if (dateKey !== currentDate) {
          if (currentDate !== null) {
            widget.addSpacer(6);
          }
          currentDate = dateKey;

          const dayHeader = widget.addText(this.getFullDate(item.date));
          dayHeader.font = Font.systemFont(11);
          dayHeader.textColor = COLORS.primary;
        }

        // Если выходной
        if (item.isFreeDay) {
          const freeText = widget.addText("Выходной");
          freeText.font = Font.systemFont(13);
          freeText.textColor = COLORS.textSecondary;
          itemsShown++;
          continue;
        }

        const lesson = item.lesson;

        // Строка с парой
        const lessonStack = widget.addStack();
        lessonStack.layoutHorizontally();

        // Левая часть: время вертикально
        const timeStack = lessonStack.addStack();
        timeStack.layoutVertically();
        timeStack.size = new Size(50, 0);

        const timeStartText = timeStack.addText(lesson.time_start);
        timeStartText.font = Font.systemFont(13);
        timeStartText.textColor = COLORS.textSecondary;

        const timeEndText = timeStack.addText(lesson.time_end);
        timeEndText.font = Font.systemFont(13);
        timeEndText.textColor = COLORS.textSecondary;

        // Правая часть: предмет, аудитория, преподаватель
        const infoStack = lessonStack.addStack();
        infoStack.layoutVertically();

        const subjectText = infoStack.addText(lesson.subject || "Предмет");
        subjectText.font = Font.boldSystemFont(13);
        subjectText.textColor = COLORS.textPrimary;
        subjectText.lineLimit = 1;

        const lessonType = this.getLessonType(lesson);
        const detailsText = infoStack.addText(
          `${this.formatAuditory(lesson)}${lessonType ? " - " + lessonType : ""} • ${this.getShortTeacherName(lesson)}`,
        );
        detailsText.font = Font.systemFont(13);
        detailsText.textColor = COLORS.textSecondary;
        detailsText.lineLimit = 1;

        itemsShown++;

        if (itemsShown < maxItemsToShow) {
          widget.addSpacer(4);
        }
      }
    }

    widget.refreshAfterDate = new Date(Date.now() + CACHE_DURATION);

    return widget;
  }

  // Большой виджет - полное расписание на несколько дней
  async createLargeWidget() {
    const widget = new ListWidget();
    widget.backgroundColor = COLORS.background;
    widget.setPadding(12, 16, 12, 16);
    widget.url = SCHEDULE_URL;

    const data = await this.fetchSchedule();
    // Показываем до 10 элементов с выходными
    const upcoming = this.getUpcomingLessons(data, 10, true);

    // Заголовок
    const titleText = widget.addText("📚 Ближайшие пары");
    titleText.font = Font.boldSystemFont(13);
    titleText.textColor = COLORS.primary;

    widget.addSpacer(6);

    if (upcoming.length === 0) {
      widget.addSpacer();
      const noClassText = widget.addText("Нет занятий");
      noClassText.font = Font.systemFont(13);
      noClassText.textColor = COLORS.noClasses;
      widget.addSpacer();
    } else {
      let currentDate = null;
      let lessonsShown = 0;
      const maxLessonsToShow = 6;

      for (
        let i = 0;
        i < upcoming.length && lessonsShown < maxLessonsToShow;
        i++
      ) {
        const item = upcoming[i];
        const dateKey = item.date.toDateString();

        // Новый день - показываем заголовок дня
        if (dateKey !== currentDate) {
          if (currentDate !== null) {
            widget.addSpacer(6);
          }
          currentDate = dateKey;

          const dayHeader = widget.addText(this.getFullDate(item.date));
          dayHeader.font = Font.systemFont(12);
          dayHeader.textColor = COLORS.primary;

          widget.addSpacer(2);
        }

        // Если это выходной день
        if (item.isFreeDay) {
          const freeText = widget.addText("Выходной");
          freeText.font = Font.systemFont(13);
          freeText.textColor = COLORS.textSecondary;
          lessonsShown++;
          continue;
        }

        const lesson = item.lesson;

        // Строка с парой
        const lessonStack = widget.addStack();
        lessonStack.layoutHorizontally();

        // Левая часть: время вертикально
        const timeStack = lessonStack.addStack();
        timeStack.layoutVertically();
        timeStack.size = new Size(55, 0);

        const timeStartText = timeStack.addText(lesson.time_start);
        timeStartText.font = Font.systemFont(13);
        timeStartText.textColor = COLORS.textSecondary;

        const timeEndText = timeStack.addText(lesson.time_end);
        timeEndText.font = Font.systemFont(13);
        timeEndText.textColor = COLORS.textSecondary;

        // Правая часть: предмет, аудитория, преподаватель
        const infoStack = lessonStack.addStack();
        infoStack.layoutVertically();

        const subjectText = infoStack.addText(lesson.subject || "Предмет");
        subjectText.font = Font.boldSystemFont(13);
        subjectText.textColor = COLORS.textPrimary;
        subjectText.lineLimit = 1;
        subjectText.minimumScaleFactor = 0.5;

        const audText = infoStack.addText(this.formatAuditoryWithType(lesson));
        audText.font = Font.systemFont(12);
        audText.textColor = COLORS.textSecondary;
        audText.lineLimit = 1;
        audText.minimumScaleFactor = 0.5;

        const teacherText = infoStack.addText(this.getFullTeacherName(lesson));
        teacherText.font = Font.systemFont(12);
        teacherText.textColor = COLORS.textSecondary;
        teacherText.lineLimit = 1;
        teacherText.minimumScaleFactor = 0.5;

        lessonsShown++;

        if (lessonsShown < maxLessonsToShow) {
          widget.addSpacer(4);
        }
      }
    }

    widget.refreshAfterDate = new Date(Date.now() + CACHE_DURATION);

    return widget;
  }

  // Создание виджета в зависимости от размера
  async createWidget(size) {
    if (!GROUP_ID) {
      return this.createErrorWidget(
        "Укажите номер группы в настройках скрипта",
      );
    }

    const widgetSize = size || config.widgetFamily || "medium";

    switch (widgetSize) {
      case "small":
        return await this.createSmallWidget();
      case "large":
        return await this.createLargeWidget();
      default:
        return await this.createMediumWidget();
    }
  }

  // Виджет с ошибкой
  createErrorWidget(message) {
    const widget = new ListWidget();
    widget.backgroundColor = COLORS.background;

    const stack = widget.addStack();
    stack.layoutVertically();
    stack.centerAlignContent();

    const icon = stack.addText("⚠️");
    icon.font = Font.systemFont(32);
    icon.centerAlignText();

    stack.addSpacer(8);

    const text = stack.addText(message);
    text.font = Font.systemFont(12);
    text.textColor = COLORS.error;
    text.centerAlignText();

    return widget;
  }
}

// ============== ЗАПУСК ==============

// Проверяем аргумент для сброса настроек
const widgetArgs = typeof args !== "undefined" ? args : {};
const queryParams = widgetArgs.queryParameters || {};
if (widgetArgs.widgetParameter === "reset" || queryParams.action === "reset") {
  if (!config.runsInWidget) {
    await resetConfig();
    const alert = new Alert();
    alert.title = "Настройки сброшены";
    alert.message = "Запустите скрипт снова для настройки новой группы.";
    alert.addAction("OK");
    await alert.present();
    Script.complete();
  }
}

// Загружаем конфигурацию группы
const configLoaded = await loadGroupConfig();

const scheduleWidget = new ScheduleWidget();
let widget;

if (!configLoaded || !GROUP_ID) {
  if (config.runsInWidget) {
    // Если виджет запущен без конфига - показываем инструкцию
    widget = scheduleWidget.createErrorWidget(
      "Откройте скрипт в Scriptable для настройки группы",
    );
  } else {
    // Если запущен напрямую и настройка отменена
    Script.complete();
  }
} else {
  widget = await scheduleWidget.createWidget();
}

if (widget) {
  if (config.runsInWidget) {
    Script.setWidget(widget);
  } else {
    // Меню для запуска напрямую
    const menu = new Alert();
    menu.title = "Расписание СПбПУ";
    menu.message = `Группа: ${GROUP_NAME}\n\nВыберите действие:`;
    menu.addAction("Показать виджет (маленький)");
    menu.addAction("Показать виджет (средний)");
    menu.addAction("Показать виджет (большой)");
    menu.addDestructiveAction("Сменить группу");
    menu.addCancelAction("Закрыть");

    const menuChoice = await menu.present();

    switch (menuChoice) {
      case 0:
        widget = await scheduleWidget.createWidget("small");
        widget.presentSmall();
        break;
      case 1:
        widget = await scheduleWidget.createWidget("medium");
        widget.presentMedium();
        break;
      case 2:
        widget = await scheduleWidget.createWidget("large");
        widget.presentLarge();
        break;
      case 3:
        // Сменить группу
        await resetConfig();
        const newConfigLoaded = await loadGroupConfig();
        if (newConfigLoaded) {
          widget = await scheduleWidget.createWidget("medium");
          widget.presentMedium();
        }
        break;
      default:
        // Закрыть - ничего не делаем
        break;
    }
  }
}

Script.complete();
