import json
import asyncio
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from openai import RateLimitError, APIError
from config.settings import settings


class OpenAIClient:
    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY не установлен. Добавьте его в .env файл.")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.timeout = 300.0
        self.max_retries = 3
        self.base_delay = 2.0

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, retry_count: int = 0) -> str:
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3
            )
            return response.choices[0].message.content or ""
        except RateLimitError as e:
            if retry_count < self.max_retries:
                delay = self.base_delay * (2 ** retry_count)
                print(f"Rate limit достигнут. Ожидание {delay:.1f} секунд перед повтором...")
                await asyncio.sleep(delay)
                return await self.generate(prompt, system_prompt, retry_count + 1)
            else:
                raise Exception(f"Превышен лимит запросов OpenAI. Проверьте квоту на https://platform.openai.com/account/billing")
        except APIError as e:
            if "insufficient_quota" in str(e).lower():
                raise Exception(f"Превышена квота OpenAI. Пополните баланс на https://platform.openai.com/account/billing")
            raise Exception(f"OpenAI API error: {e}")
        except Exception as e:
            raise Exception(f"OpenAI API error: {e}")

    async def extract_tasks(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        system_prompt = """Ты — эксперт по анализу диалогов. Твоя задача — найти все требования, запросы, задачи и пожелания клиента.

Верни результат в формате JSON массива, где каждый элемент:
{
  "description": "описание задачи",
  "message_id": номер_сообщения,
  "priority": "low|medium|high|critical",
  "context": "контекст из диалога"
}

Если задач нет — верни пустой массив [].

Важно: фиксируй только реальные задачи клиента, не общие фразы."""

        messages_text = "\n\n".join([
            f"[{msg['id']}] {msg['role']}: {msg['text']}"
            for msg in messages
        ])
        
        prompt = f"""Проанализируй диалог и найди все задачи клиента:

{messages_text}

Верни только JSON массив с задачами, без дополнительного текста."""

        response = await self.generate(prompt, system_prompt)
        
        try:
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            tasks = json.loads(cleaned_response)
            if isinstance(tasks, list):
                return tasks
            return []
        except Exception as e:
            return []

    async def check_task_completion(self, task: Dict[str, Any], responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        system_prompt = """Ты — эксперт по анализу выполнения задач. Определи, была ли задача выполнена разработчиком."""

        task_text = f"Задача: {task['description']}\nИз сообщения: {task.get('context', '')}"
        responses_text = "\n\n".join([
            f"[{r['id']}] {r['text']}"
            for r in responses
        ])
        
        prompt = f"""Задача клиента:
{task_text}

Ответы разработчика:
{responses_text}

Определи:
1. Была ли задача выполнена? (true/false)
2. Если да — в каком сообщении есть подтверждение?
3. Если нет — почему?

Верни JSON:
{{
  "completed": true/false,
  "response_message_id": номер_или_null,
  "evidence": "доказательство выполнения или причина пропуска"
}}"""

        response = await self.generate(prompt, system_prompt)
        
        try:
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            result = json.loads(cleaned_response)
            return result
        except Exception as e:
            return {"completed": False, "response_message_id": None, "evidence": "Не удалось определить"}
