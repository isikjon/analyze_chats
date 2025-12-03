import asyncio
import sys
from pathlib import Path
from typing import Optional
from services.telegram_client import TelegramImporter
from services.chat_parser import ChatParser
from services.task_extractor import TaskExtractor
from services.task_matcher import TaskMatcher
from services.report_generator import ReportGenerator


async def import_from_telegram_api(chat_id: Optional[int] = None, username: Optional[str] = None) -> Optional[object]:
    importer = TelegramImporter()
    try:
        print("Подключение к Telegram...")
        if not await importer.connect():
            print("Ошибка: не удалось подключиться к Telegram")
            print("Проверьте TELEGRAM_API_ID и TELEGRAM_API_HASH в .env")
            return None
        
        if username:
            print(f"Поиск чата по username: @{username}...")
            found_chat_id = await importer.find_chat_by_username(username)
            if not found_chat_id:
                print(f"Чат с username @{username} не найден")
                print("Попытка поиска по частичному совпадению...")
                results = await importer.search_chats_by_username(username)
                if results:
                    print("\nНайдены похожие чаты:")
                    for i, chat in enumerate(results, 1):
                        print(f"  {i}. @{chat.get('username', 'N/A')} - {chat['title']} (ID: {chat['id']})")
                    print("\nИспользуется первый найденный чат.")
                    found_chat_id = results[0]['id']
                else:
                    return None
            chat_id = found_chat_id
        
        if not chat_id:
            print("Ошибка: не указан chat_id или username")
            return None
        
        print(f"Импорт чата (ID: {chat_id})...")
        session = await importer.import_chat(chat_id)
        print(f"Импортировано сообщений: {session.total_messages}")
        return session
    finally:
        await importer.disconnect()


def import_from_file(file_path: Path) -> Optional[object]:
    parser = ChatParser()
    
    if file_path.suffix == ".json":
        print("Парсинг JSON экспорта Telegram...")
        return parser.parse_telegram_export(file_path)
    elif file_path.suffix == ".txt":
        print("Парсинг TXT файла...")
        return parser.parse_txt(file_path)
    else:
        print(f"Неподдерживаемый формат: {file_path.suffix}")
        return None


async def analyze_chat(session):
    print("\n" + "=" * 80)
    print("АНАЛИЗ ЧАТА")
    print("=" * 80)
    
    print(f"Чат: {session.chat_title or session.chat_id}")
    print(f"Сообщений: {session.total_messages}")
    print(f"Источник: {session.source}\n")
    
    print("Извлечение задач...")
    extractor = TaskExtractor()
    tasks = await extractor.extract_tasks(session)
    print(f"Найдено задач: {len(tasks)}\n")
    
    if not tasks:
        print("Задачи не найдены.")
        return
    
    print("Сопоставление задач с ответами...")
    matcher = TaskMatcher()
    tasks = await matcher.match_tasks_with_responses(session, tasks)
    
    completed = sum(1 for t in tasks if t.status.value == "completed")
    missed = sum(1 for t in tasks if t.status.value == "missed")
    
    print(f"Выполнено: {completed}")
    print(f"Пропущено: {missed}\n")
    
    print("Генерация отчета...")
    generator = ReportGenerator()
    report = generator.generate(session.chat_id, session.chat_title, tasks)
    
    json_path = generator.save_json(report)
    txt_path = generator.save_txt(report)
    
    print("\n" + "=" * 80)
    print("ОТЧЕТ СОЗДАН")
    print("=" * 80)
    print(f"JSON: {json_path}")
    print(f"TXT: {txt_path}")
    print("\nСтатистика:")
    print(f"  Всего задач: {report.summary.total_tasks}")
    print(f"  Выполнено: {report.summary.completed_tasks}")
    print(f"  Пропущено: {report.summary.missed_tasks}")
    print(f"  В процессе: {report.summary.in_progress_tasks}")
    print(f"  Ожидают: {report.summary.pending_tasks}")


async def main():
    print("=" * 80)
    print("АНАЛИЗАТОР ЧАТОВ - ВЫЯВЛЕНИЕ ПРОПУЩЕННЫХ ЗАДАЧ")
    print("=" * 80)
    print()
    
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python main.py telegram <chat_id>     - импорт из Telegram API по ID")
        print("  python main.py telegram @username     - импорт из Telegram API по username")
        print("  python main.py file <путь_к_файлу>     - импорт из файла (.json, .txt)")
        print()
        print("Примеры:")
        print("  python main.py telegram 123456789")
        print("  python main.py telegram @channel_name")
        print("  python main.py telegram username")
        print("  python main.py file chat_export.json")
        print("  python main.py file conversation.txt")
        sys.exit(1)
    
    source_type = sys.argv[1].lower()
    
    if source_type == "telegram":
        if len(sys.argv) < 3:
            print("Ошибка: укажите chat_id или username")
            sys.exit(1)
        
        identifier = sys.argv[2]
        
        if identifier.startswith('@') or not identifier.isdigit():
            username = identifier.lstrip('@')
            session = await import_from_telegram_api(username=username)
        else:
            try:
                chat_id = int(identifier)
                session = await import_from_telegram_api(chat_id=chat_id)
            except ValueError:
                print("Ошибка: chat_id должен быть числом, или используйте @username")
                sys.exit(1)
        
        if not session:
            sys.exit(1)
    
    elif source_type == "file":
        if len(sys.argv) < 3:
            print("Ошибка: укажите путь к файлу")
            sys.exit(1)
        
        file_path = Path(sys.argv[2])
        if not file_path.exists():
            print(f"Ошибка: файл не найден: {file_path}")
            sys.exit(1)
        
        session = import_from_file(file_path)
        if not session:
            sys.exit(1)
    
    else:
        print(f"Ошибка: неизвестный тип источника: {source_type}")
        print("Используйте 'telegram' или 'file'")
        sys.exit(1)
    
    await analyze_chat(session)


if __name__ == "__main__":
    asyncio.run(main())
