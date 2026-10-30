import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from domain.playground import getChatTitleDomain
from utils.error import DBError



class ChatTitleQuery:
    @staticmethod
    async def insert_chat_title(db:AsyncSession, domain_data:getChatTitleDomain):
        try:
            query = text("INSERT INTO chat_title (session_key, company_key, title, reg_date, update_date, user_id) VALUES (:session_key, :company_key, :title, :reg_date, :update_date, :user_id)")
            params = {"session_key": domain_data.session_key, "company_key": domain_data.company_key, "title": domain_data.title, "reg_date": domain_data.current_date, "update_date": domain_data.current_date, "user_id": domain_data.user_id}
            await db.execute(query, params)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.chat_title.ChatTitleQuery.insert_chat_title] DBError: {e}")
            raise DBError(e)

    
    @staticmethod
    async def get_chat_title(db:AsyncSession, domain_data:getChatTitleDomain):
        try:
            if domain_data.session_key:
                query = text("SELECT session_key, title, update_date FROM chat_title WHERE session_key = :session_key ORDER BY update_date DESC")
                params = {"session_key": domain_data.session_key}
                
            elif domain_data.user_id:
                query = text("SELECT session_key, title, update_date FROM chat_title WHERE user_id = :user_id ORDER BY update_date DESC")
                params = {"user_id": domain_data.user_id}
            else:
                raise DBError("session_key or user_id is required")
            
            execute = await db.execute(query, params)
            results = execute.fetchall()
            
            return [{"sessionKey":result[0], "title": result[1], "date": result[2]} for result in results] if results else None

        except Exception as e:
            logging.error(f"[queries.chat_title.ChatTitleQuery.get_chat_title] DBError: {e}")
            raise DBError(e)

    
    @staticmethod
    async def update_chat_title(db:AsyncSession, session_key:str, title:str, current_date:datetime):
        try:
            query = text("UPDATE chat_title SET title = :title, update_date = :update_date WHERE session_key = :session_key")
            params = {"title": title, "update_date": current_date, "session_key": session_key}
            await db.execute(query, params)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.chat_title.ChatTitleQuery.update_chat_title] DBError: {e}")
            raise DBError(e)