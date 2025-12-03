# Анализатор чатов - Выявление пропущенных задач

Приложение для автоматического анализа чатов с клиентами и выявления пропущенных задач с использованием OpenAI API.

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Настройте `.env` файл (скопируйте `.env.example`):
```bash
cp .env.example .env
```

3. Заполните настройки в `.env`:
- `OPENAI_API_KEY` - ваш API ключ OpenAI (получите на https://platform.openai.com/api-keys)
- `OPENAI_MODEL` - модель для анализа (по умолчанию gpt-4o-mini)
- `TELEGRAM_API_ID` и `TELEGRAM_API_HASH` - для импорта из Telegram API (получите на https://my.telegram.org)
- `TELEGRAM_PHONE` - ваш номер телефона для Telegram

## Использование

### Импорт из Telegram API:
```bash
python main.py telegram <chat_id>
```

### Импорт из файла:
```bash
python main.py file <путь_к_файлу>
```

Поддерживаемые форматы:
- `.json` - экспорт Telegram Desktop
- `.txt` - текстовый файл с диалогом

## Результаты

Отчеты сохраняются в папке `reports/`:
- JSON формат - для программной обработки
- TXT формат - для чтения человеком

## Архитектура

Микросервисная архитектура:
- `main.py` - точка входа
- `services/` - бизнес-логика
- `models/` - модели данных
- `config/` - конфигурация
# analyze_chats
