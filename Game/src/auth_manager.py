
import os
import json
from datetime import datetime

from config import Config


class AuthManager:
    def __init__(self):
        self.session_file = Config.SESSION_FILE
        self.token = None
        self.user = None
        self._load_session()
    
    def save_session(self, token, user_data):
        """Сохраняет сессию (токен и данные пользователя)"""
        self.token = token
        self.user = user_data
        
        session_data = {
            "token": token,
            "user": user_data,
            "updated_at": datetime.now().isoformat()
        }
        
        try:
            os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
            
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            username = user_data.get('username', 'Unknown') if user_data else 'Unknown'
            print(f"Сессия сохранена для: {username}")
            return True
        except Exception as e:
            print(f"Ошибка сохранения сессии: {e}")
            return False
    
    def _load_session(self):
        """Загружает сессию из файла"""
        try:
            if not os.path.exists(self.session_file):
                print("Файл сессии не найден")
                return False
            
            if os.path.getsize(self.session_file) == 0:
                print("Файл сессии пуст")
                return False
            
            with open(self.session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            self.token = session_data.get("token")
            self.user = session_data.get("user")
            
            if self.token and self.user:
                username = self.user.get('username', 'Unknown')
                print(f"Сессия загружена для: {username}")
                return True
            else:
                print("Сессия неполная (отсутствует токен или пользователь)")
                self.clear_session()
                return False
                
        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга сессии: {e}")
            self.clear_session()
            return False
        except Exception as e:
            print(f"Ошибка загрузки сессии: {e}")
            self.clear_session()
            return False
    
    def clear_session(self):
        """Очищает сессию. НЕ удаляет скины!"""
        self.token = None
        self.user = None
        
        try:
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
                print("Сессия удалена")
            return True
        except Exception as e:
            print(f"Ошибка удаления сессии: {e}")
            return False
    
    def refresh_session(self):
        """Принудительно перезагружает сессию из файла"""
        self._load_session()
        return self.is_authenticated()
    
    def is_authenticated(self):
        """Проверяет, авторизован ли пользователь"""
        if self.token is None or self.user is None:
            self._load_session()
        return self.token is not None and self.user is not None
    
    def get_auth_header(self):
        """Возвращает заголовок для авторизованных запросов"""
        if self.is_authenticated():
            return {"Authorization": f"Bearer {self.token}"}
        return {}
    
    def get_username(self):
        """Возвращает имя пользователя"""
        if self.user:
            return self.user.get("username", "")
        return ""
    
    def get_balance(self):
        """Возвращает баланс пользователя"""
        if self.user:
            return self.user.get("balance", 0)
        return 0
    
    def get_best_score(self):
        """Возвращает лучший счёт пользователя"""
        if self.user:
            return self.user.get("bestScore", 0)
        return 0
    
    def update_user_data(self, new_data):
        """Обновляет данные пользователя в сессии"""
        if not self.is_authenticated():
            print("Не авторизован, нельзя обновить данные")
            return False
        
        if self.user:
            self.user.update(new_data)
            return self.save_session(self.token, self.user)
        return False
