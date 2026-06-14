import sqlite3
import uuid
from typing import List


class ChatRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                user_message TEXT,
                ai_response TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions (session_id)
            )
        ''')
        
        cursor.execute("PRAGMA table_info(chat_sessions)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'title' not in columns:
            cursor.execute('ALTER TABLE chat_sessions ADD COLUMN title TEXT')
        
        self.conn.commit()
    
    def create_session(self, user_id: str = "default_user") -> str:
        session_id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO chat_sessions (session_id, user_id) 
            VALUES (?, ?)
        ''', (session_id, user_id))
        self.conn.commit()
        return session_id
    
    def session_exists(self, session_id: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute('SELECT 1 FROM chat_sessions WHERE session_id = ?', (session_id,))
        return cursor.fetchone() is not None
    
    def update_session_title(self, session_id: str, title: str):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE chat_sessions 
            SET title = ? 
            WHERE session_id = ?
        ''', (title, session_id))
        self.conn.commit()
    
    def delete_session(self, session_id: str):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM chat_messages WHERE session_id = ?', (session_id,))
        cursor.execute('DELETE FROM chat_sessions WHERE session_id = ?', (session_id,))
        self.conn.commit()
    
    def save_message(self, session_id: str, user_message: str, ai_response: str):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO chat_messages (session_id, user_message, ai_response)
            VALUES (?, ?, ?)
        ''', (session_id, user_message, ai_response))
        
        cursor.execute('''
            UPDATE chat_sessions 
            SET last_activity = CURRENT_TIMESTAMP 
            WHERE session_id = ?
        ''', (session_id,))
        
        self.conn.commit()
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT user_message, ai_response, timestamp
            FROM chat_messages 
            WHERE session_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (session_id, limit))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'user': row[0],
                'assistant': row[1],
                'timestamp': row[2]
            })
        
        return list(reversed(history))
    
    def get_message_count(self, session_id: str) -> int:
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM chat_messages WHERE session_id = ?', (session_id,))
        return cursor.fetchone()[0]
    
    def get_all_sessions(self) -> List[dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT 
                s.session_id,
                s.user_id,
                s.title,
                s.created_at,
                s.last_activity,
                COUNT(m.id) as message_count
            FROM chat_sessions s
            LEFT JOIN chat_messages m ON s.session_id = m.session_id
            GROUP BY s.session_id
            ORDER BY s.last_activity DESC
        ''')
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                'session_id': row[0],
                'user_id': row[1],
                'title': row[2],
                'created_at': row[3],
                'last_activity': row[4],
                'message_count': row[5]
            })
        
        return sessions
