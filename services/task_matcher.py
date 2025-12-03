import asyncio
from typing import List
from models.chat import ChatSession, ChatMessage, MessageRole
from models.task import Task, TaskStatus
from services.openai_client import OpenAIClient


class TaskMatcher:
    def __init__(self):
        self.ai_client = OpenAIClient()

    async def match_tasks_with_responses(self, session: ChatSession, tasks: List[Task]) -> List[Task]:
        total_tasks = len(tasks)
        print(f"Проверка выполнения {total_tasks} задач...")
        
        for i, task in enumerate(tasks, 1):
            try:
                print(f"  Задача {i}/{total_tasks}...", end=" ", flush=True)
                
                source_msg = next((m for m in session.messages if m.id == task.source_message_id), None)
                if not source_msg:
                    task.status = TaskStatus.MISSED
                    task.missed_reason = "Исходное сообщение не найдено"
                    print("пропущена (сообщение не найдено)")
                    continue
                
                responses = self._get_responses_after(session, source_msg)
                
                if not responses:
                    task.status = TaskStatus.MISSED
                    task.missed_reason = "Нет ответов после запроса"
                    print("пропущена (нет ответов)")
                    continue
                
                responses_data = [{"id": r.id, "text": r.text} for r in responses]
                task_data = {
                    "description": task.description,
                    "context": task.context or ""
                }
                
                result = await self.ai_client.check_task_completion(task_data, responses_data)
                
                if result.get("completed", False):
                    task.status = TaskStatus.COMPLETED
                    task.response_message_id = result.get("response_message_id")
                    task.completion_evidence = result.get("evidence", "")
                    if task.response_message_id:
                        response_msg = next((m for m in session.messages if m.id == task.response_message_id), None)
                        if response_msg:
                            task.response_message_text = response_msg.text
                            task.completed_at = response_msg.timestamp
                    print("выполнена")
                else:
                    task.status = TaskStatus.MISSED
                    task.missed_reason = result.get("evidence", "Задача не была выполнена")
                    print("пропущена")
                
                await asyncio.sleep(0.3)
            except Exception as e:
                print(f"ошибка: {e}")
                task.status = TaskStatus.MISSED
                task.missed_reason = f"Ошибка при проверке: {str(e)}"
                continue
        
        return tasks

    def _get_responses_after(self, session: ChatSession, source_msg: ChatMessage, limit: int = 10) -> List[ChatMessage]:
        responses = []
        found_source = False
        
        for msg in session.messages:
            if msg.id == source_msg.id:
                found_source = True
                continue
            
            if found_source and msg.role == MessageRole.DEVELOPER:
                responses.append(msg)
                if len(responses) >= limit:
                    break
        
        return responses
