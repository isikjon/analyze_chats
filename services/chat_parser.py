import json
from pathlib import Path
from datetime import datetime
from models.chat import ChatSession, ChatMessage, MessageRole


class ChatParser:
    @staticmethod
    def parse_telegram_export(file_path: Path) -> ChatSession:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        messages_list = []
        chat_name = data.get("name", "Unknown")
        
        for msg_data in data.get("messages", []):
            if msg_data.get("type") != "message" or not msg_data.get("text"):
                continue
            
            text = msg_data.get("text")
            if isinstance(text, list):
                text = " ".join([item.get("text", "") for item in text if isinstance(item, dict)])
            
            role = MessageRole.CLIENT
            if msg_data.get("from") and isinstance(msg_data.get("from"), str):
                if "bot" in msg_data.get("from", "").lower() or "developer" in msg_data.get("from", "").lower():
                    role = MessageRole.DEVELOPER
            
            date_str = msg_data.get("date", "")
            try:
                timestamp = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except:
                timestamp = datetime.now()
            
            reply_to_id = msg_data.get("reply_to_message_id")
            
            chat_msg = ChatMessage(
                id=msg_data.get("id", len(messages_list) + 1),
                text=text,
                role=role,
                timestamp=timestamp,
                reply_to_message_id=reply_to_id,
                raw_data=msg_data
            )
            messages_list.append(chat_msg)
        
        for msg in messages_list:
            if msg.reply_to_message_id:
                for other_msg in messages_list:
                    if other_msg.id == msg.reply_to_message_id:
                        msg.reply_to_message = other_msg
                        break
        
        return ChatSession(
            chat_id=str(file_path.stem),
            chat_title=chat_name,
            source="telegram_export",
            messages=messages_list,
            total_messages=len(messages_list)
        )

    @staticmethod
    def parse_txt(file_path: Path) -> ChatSession:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        messages_list = []
        current_role = MessageRole.UNKNOWN
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("Клиент:") or line.startswith("Client:"):
                current_role = MessageRole.CLIENT
                text = line.split(":", 1)[1].strip()
            elif line.startswith("Разработчик:") or line.startswith("Developer:"):
                current_role = MessageRole.DEVELOPER
                text = line.split(":", 1)[1].strip()
            else:
                text = line
            
            if text:
                chat_msg = ChatMessage(
                    id=i,
                    text=text,
                    role=current_role,
                    timestamp=datetime.now(),
                    raw_data={"line_number": i}
                )
                messages_list.append(chat_msg)
        
        return ChatSession(
            chat_id=str(file_path.stem),
            chat_title=file_path.stem,
            source="txt",
            messages=messages_list,
            total_messages=len(messages_list)
        )

