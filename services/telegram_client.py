import asyncio
from typing import List, Optional
from datetime import datetime
from telethon import TelegramClient
from telethon.tl.types import Message, User, Chat, Channel
from config.settings import settings
from models.chat import ChatSession, ChatMessage, MessageRole


class TelegramImporter:
    def __init__(self):
        self.api_id = settings.telegram_api_id
        self.api_hash = settings.telegram_api_hash
        self.phone = settings.telegram_phone
        self.session_name = settings.telegram_session_name
        self.client: Optional[TelegramClient] = None

    async def connect(self) -> bool:
        if not all([self.api_id, self.api_hash]):
            return False
        
        try:
            self.client = TelegramClient(
                self.session_name,
                int(self.api_id),
                self.api_hash
            )
            await self.client.start(phone=self.phone)
            return True
        except Exception as e:
            print(f"Ошибка подключения к Telegram: {e}")
            return False

    async def disconnect(self):
        if self.client:
            await self.client.disconnect()

    async def get_chats(self) -> List[dict]:
        if not self.client:
            return []
        
        chats = []
        async for dialog in self.client.iter_dialogs():
            chats.append({
                "id": dialog.id,
                "title": dialog.name,
                "type": "channel" if dialog.is_channel else "group" if dialog.is_group else "user"
            })
        return chats

    async def find_chat_by_username(self, username: str) -> Optional[int]:
        if not self.client:
            return None
        
        username = username.lstrip('@')
        
        try:
            entity = await self.client.get_entity(username)
            return entity.id
        except Exception as e:
            print(f"Ошибка поиска чата по username '{username}': {e}")
            return None

    async def search_chats_by_username(self, username: str) -> List[dict]:
        if not self.client:
            return []
        
        username = username.lstrip('@').lower()
        results = []
        
        async for dialog in self.client.iter_dialogs():
            dialog_username = None
            if hasattr(dialog.entity, 'username') and dialog.entity.username:
                dialog_username = dialog.entity.username.lower()
            
            if dialog_username and username in dialog_username:
                results.append({
                    "id": dialog.id,
                    "title": dialog.name,
                    "username": dialog.entity.username,
                    "type": "channel" if dialog.is_channel else "group" if dialog.is_group else "user"
                })
        
        return results

    async def import_chat(self, chat_id: int, limit: Optional[int] = None) -> ChatSession:
        if not self.client:
            raise Exception("Не подключен к Telegram")
        
        entity = await self.client.get_entity(chat_id)
        chat_title = getattr(entity, "title", None) or getattr(entity, "first_name", "Unknown")
        
        messages_list = []
        async for message in self.client.iter_messages(entity, limit=limit):
            if not message.text:
                continue
            
            role = MessageRole.CLIENT
            if message.out:
                role = MessageRole.DEVELOPER
            
            reply_to_id = message.reply_to_msg_id if message.reply_to else None
            
            chat_msg = ChatMessage(
                id=message.id,
                text=message.text,
                role=role,
                timestamp=message.date,
                reply_to_message_id=reply_to_id,
                raw_data={
                    "sender_id": message.sender_id,
                    "date": message.date.isoformat() if message.date else None
                }
            )
            messages_list.append(chat_msg)
        
        messages_list.reverse()
        
        for msg in messages_list:
            if msg.reply_to_message_id:
                for other_msg in messages_list:
                    if other_msg.id == msg.reply_to_message_id:
                        msg.reply_to_message = other_msg
                        break
        
        session = ChatSession(
            chat_id=str(chat_id),
            chat_title=chat_title,
            source="telegram_api",
            messages=messages_list,
            total_messages=len(messages_list)
        )
        
        return session

