import asyncio
from typing import List, Dict, Any
from datetime import datetime
from models.chat import ChatSession, ChatMessage
from models.task import Task, TaskStatus, TaskPriority
from services.openai_client import OpenAIClient


class TaskExtractor:
    def __init__(self):
        self.ai_client = OpenAIClient()

    async def extract_tasks(self, session: ChatSession) -> List[Task]:
        messages_data = []
        for msg in session.messages:
            if msg.role.value == "client":
                messages_data.append({
                    "id": msg.id,
                    "role": msg.role.value,
                    "text": msg.text
                })
        
        if not messages_data:
            return []
        
        chunks = self._chunk_messages(messages_data, chunk_size=30)
        all_tasks = []
        total_chunks = len(chunks)
        
        print(f"Обработка {total_chunks} частей чата...")
        
        for i, chunk in enumerate(chunks, 1):
            try:
                print(f"  Часть {i}/{total_chunks}...", end=" ", flush=True)
                tasks_data = await self.ai_client.extract_tasks(chunk)
                print(f"найдено задач: {len(tasks_data)}")
                
                for task_data in tasks_data:
                    message_id = task_data.get("message_id", 0)
                    source_msg = next((m for m in session.messages if m.id == message_id), None)
                    
                    if not source_msg:
                        continue
                    
                    priority_str = task_data.get("priority", "medium").lower()
                    try:
                        priority = TaskPriority(priority_str)
                    except:
                        priority = TaskPriority.MEDIUM
                    
                    task = Task(
                        id=f"{session.chat_id}_{message_id}_{len(all_tasks)}",
                        description=task_data.get("description", ""),
                        source_message_id=message_id,
                        source_message_text=source_msg.text,
                        status=TaskStatus.PENDING,
                        priority=priority,
                        requested_at=source_msg.timestamp,
                        context=task_data.get("context", "")
                    )
                    all_tasks.append(task)
                
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"Ошибка при обработке части {i}: {e}")
                continue
        
        return all_tasks

    def _chunk_messages(self, messages: List[Dict], chunk_size: int) -> List[List[Dict]]:
        chunks = []
        for i in range(0, len(messages), chunk_size):
            chunks.append(messages[i:i + chunk_size])
        return chunks
