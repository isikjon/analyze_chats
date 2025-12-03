import json
from pathlib import Path
from datetime import datetime
from typing import List
from models.task import Task, TaskStatus
from models.report import AnalysisReport, ReportSummary
from config.settings import settings


class ReportGenerator:
    def __init__(self):
        self.reports_path = settings.reports_path

    def generate(self, chat_id: str, chat_title: str, tasks: List[Task]) -> AnalysisReport:
        missed_tasks = [t for t in tasks if t.status == TaskStatus.MISSED]
        completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED]
        pending_tasks = [t for t in tasks if t.status == TaskStatus.PENDING]
        in_progress_tasks = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
        
        summary = ReportSummary(
            total_tasks=len(tasks),
            completed_tasks=len(completed_tasks),
            pending_tasks=len(pending_tasks),
            missed_tasks=len(missed_tasks),
            in_progress_tasks=len(in_progress_tasks)
        )
        
        report = AnalysisReport(
            chat_id=chat_id,
            chat_title=chat_title,
            summary=summary,
            tasks=tasks,
            missed_tasks=missed_tasks
        )
        
        return report

    def save_json(self, report: AnalysisReport) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{report.chat_id}_{timestamp}.json"
        filepath = self.reports_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report.model_dump(mode='json'), f, ensure_ascii=False, indent=2, default=str)
        
        return filepath

    def save_txt(self, report: AnalysisReport) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{report.chat_id}_{timestamp}.txt"
        filepath = self.reports_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"ОТЧЕТ ПО АНАЛИЗУ ЧАТА\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Чат: {report.chat_title or report.chat_id}\n")
            f.write(f"Дата анализа: {report.analyzed_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("СТАТИСТИКА:\n")
            f.write("-" * 80 + "\n")
            f.write(f"Всего задач: {report.summary.total_tasks}\n")
            f.write(f"Выполнено: {report.summary.completed_tasks}\n")
            f.write(f"В процессе: {report.summary.in_progress_tasks}\n")
            f.write(f"Ожидают: {report.summary.pending_tasks}\n")
            f.write(f"Пропущено: {report.summary.missed_tasks}\n\n")
            
            if report.missed_tasks:
                f.write("=" * 80 + "\n")
                f.write("ПРОПУЩЕННЫЕ ЗАДАЧИ:\n")
                f.write("=" * 80 + "\n\n")
                
                for i, task in enumerate(report.missed_tasks, 1):
                    f.write(f"{i}. ЗАДАЧА #{task.id}\n")
                    f.write(f"   Описание: {task.description}\n")
                    f.write(f"   Приоритет: {task.priority.value}\n")
                    f.write(f"   Сообщение #{task.source_message_id}: {task.source_message_text[:100]}...\n")
                    f.write(f"   Причина пропуска: {task.missed_reason or 'Не указана'}\n")
                    f.write(f"   Запрошено: {task.requested_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    if task.context:
                        f.write(f"   Контекст: {task.context}\n")
                    f.write("\n")
            
            f.write("=" * 80 + "\n")
            f.write("ВСЕ ЗАДАЧИ:\n")
            f.write("=" * 80 + "\n\n")
            
            for i, task in enumerate(report.tasks, 1):
                f.write(f"{i}. [{task.status.value.upper()}] {task.description}\n")
                f.write(f"   Сообщение #{task.source_message_id}\n")
                if task.status == TaskStatus.COMPLETED and task.completion_evidence:
                    f.write(f"   Выполнено: {task.completion_evidence}\n")
                elif task.status == TaskStatus.MISSED:
                    f.write(f"   Пропущено: {task.missed_reason or 'Не указана причина'}\n")
                f.write("\n")
        
        return filepath

