# 🌐 Browser Automation with AI Agent

Интерактивная система автоматизации браузера с поддержкой управления через естественный язык с помощью AI агента.

## ✨ Особенности

- **🤖 AI-управление** — автоматизируйте браузер через естественный язык
- **📄 Accessibility snapshots** — эффективная передача информации о странице (без изображений)
- **🔧 Инструменты для агента** — навигация, клики, ввод текста, нажатие клавиш
- **⚡ Асинхронность** — полная поддержка async/await для быстрого выполнения
- **💬 Интерактивный REPL** — управление браузером прямо из терминала

## 🚀 Быстрый старт

### Требования
- Python 3.13+
- OpenAI API ключ (для использования Claude API)

### Установка

```bash
# Установить зависимости
uv sync

# Установить браузеры Playwright
playwright install
```

### Запуск

```bash
# Интерактивный режим с пустой страницей
python -m src.app.main

# С начальным URL
python -m src.app.main --url https://example.com

# В headless режиме (без видимого окна)
python -m src.app.main --url https://example.com --headless
```

## 💻 Использование

После запуска вы попадаете в интерактивный REPL где можете вводить команды:

```
[*] Browser Automation REPL
==================================================
Starting browser with initial URL: about:blank
Type 'help' for commands, 'exit' to quit
==================================================
[+] Browser launched

> Navigate to google.com
[*] Processing: Navigate to google.com
--------------------------------------------------
[Agent response]

> Search for "python automation"
[*] Processing: Search for "python automation"
--------------------------------------------------
[Agent response]

> Take a screenshot
```

## 📚 Доступные команды

| Команда | Описание |
|---------|---------|
| `snapshot` | Показать текущий снимок страницы с element references |
| `<команда>` | Натуральная команда для AI агента |
| `help` | Справка по доступным командам |
| `exit` | Закрыть браузер и выход |

## 🎯 Примеры команд

### Навигация

```
Navigate to https://www.wikipedia.org
Go to google.com
Open amazon.com
```

### Взаимодействие с элементами

```
Click the search button
Find and click the login button
Click the "Read More" link
```

### Заполнение форм

```
Type "hello world" in the search box
Fill the email field with john@example.com
Find the password input and type secret123
```

### Нажатие клавиш

```
Press Enter to submit
Hit Escape to close the modal
Tab to the next field
```

### Комбинированные команды

```
Navigate to google.com, search for "weather in Paris", and click the first result
Fill the login form with username=admin password=test123 and click login
```

## 🔍 Как работают Element References (refs)

Aria snapshot возвращает информацию о странице с element references:

```yaml
- heading "My Website" [level=1] [ref=e1]
- paragraph [ref=e2]: Welcome to my site
- textbox "Search:" [ref=e3]
- button "Search" [ref=e4]
- link "Home" [ref=e5]
```

Каждый элемент имеет `[ref=eX]`:
- `e0`, `e1`, `e2` ... глобальные индексы элементов на странице
- AI агент видит эти refs и использует их автоматически
- **Вам не нужно запоминать refs** — агент о них знает!

## 🛠️ Архитектура

### Компоненты

**`browser.py`** — Сервис управления браузером
- Запуск/закрытие браузера через Playwright
- Получение accessibility snapshots
- Взаимодействие с элементами (клики, ввод текста, нажатие клавиш)

**`tools.py`** — Tools для AI агента
- `get_page_snapshot()` — текущий снимок страницы
- `navigate_to(url)` — перейти по URL
- `click_element(ref)` — кликнуть элемент
- `type_into_element(ref, text)` — ввести текст
- `press_key_on_element(ref, key)` — нажать клавишу
- `get_current_url()` — получить текущий URL
- `take_screenshot(filename)` — сделать скриншот

**`repl.py`** — Интерактивный REPL
- Ввод команд пользователя
- Обработка через AI агента
- Управление браузером

**`main.py`** — Точка входа
- CLI аргументы
- Запуск REPL

## 🧪 Тестирование

Проверить что все работает:

```bash
# Тест основных инструментов
python test_tools.py

# Демонстрация
python test_demo.py
```

## 📖 Дополнительные ресурсы

- [Примеры использования](docs/EXAMPLES.md)
- [Playwright документация](https://playwright.dev/python/)
- [Aria Snapshots](https://playwright.dev/python/docs/aria-snapshots)

## 🔧 Переменные окружения

Создайте `.env` файл:

```env
BASE_URL=https://api.openai.com/v1
API_KEY=sk-your-api-key-here
MODEL_NAME=gpt-4o
```

Или скопируйте из примера:

```bash
cp .env.example .env
# Отредактируйте .env с вашими данными
```

## ⚙️ Поддерживаемые браузеры

- Chromium (по умолчанию)
- Firefox (можно изменить в коде)
- WebKit (Safari)

## 🐛 Известные ограничения

- **CAPTCHA**: Не поддерживаются системы защиты от ботов
- **Модальные окна**: Иногда требуют явного закрытия перед доступом к контенту
- **Очень динамический контент**: Сложные SPA приложения могут требовать дополнительной настройки
- **PDF**: Для работы с PDF требуется дополнительная обработка

## 📝 Лицензия

MIT

---

**Создано с ❤️ для автоматизации браузера**
