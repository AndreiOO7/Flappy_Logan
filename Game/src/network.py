# src/network.py
"""
API клиент для взаимодействия с бэкендом Flappy Logan
"""

import requests
import json
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal

from config import Config


class APIThread(QThread):
    finished = pyqtSignal(bool, str, dict)
    
    def __init__(self, endpoint, method="POST", data=None, token=None, timeout=10):
        super().__init__()
        self.base_url = Config.API_URL
        self.endpoint = endpoint
        self.method = method.upper()
        self.data = data
        self.token = token
        self.timeout = timeout
    
    def run(self):
        print(f"📤 [{self.method}] {self.endpoint}")
        if self.data:
            log_data = self.data.copy() if isinstance(self.data, dict) else self.data
            if isinstance(log_data, dict) and "password" in log_data:
                log_data["password"] = "***"
            print(f"   📦 {json.dumps(log_data, ensure_ascii=False)}")
        
        try:
            url = f"{self.base_url}/{self.endpoint}"
            headers = {"Content-Type": "application/json"}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            
            if self.method == "GET":
                response = requests.get(url, headers=headers, timeout=self.timeout)
            elif self.method == "POST":
                response = requests.post(url, json=self.data, headers=headers, timeout=self.timeout)
            elif self.method == "PUT":
                response = requests.put(url, json=self.data, headers=headers, timeout=self.timeout)
            else:
                print(f"   ❌ Неизвестный метод: {self.method}")
                self.finished.emit(False, f"Неизвестный метод: {self.method}", {})
                return
            
            try:
                data = response.json()
                print(f"📥 [{response.status_code}] {self.endpoint}")
                if response.status_code in [200, 201] and data.get("success", False):
                    print(f"   ✅ Успешно")
                else:
                    error_msg = data.get("error", {}).get("message", "Ошибка")
                    print(f"   ❌ {error_msg}")
            except:
                print(f"📥 [{response.status_code}] {self.endpoint} (не JSON)")
            
            try:
                data = response.json()
            except json.JSONDecodeError:
                self.finished.emit(
                    False, 
                    f"Ошибка парсинга ответа (статус: {response.status_code})", 
                    {}
                )
                return
            
            if response.status_code in [200, 201] and data.get("success", False):
                self.finished.emit(True, "Успешно", data)
            else:
                error_msg = data.get("error", {}).get("message", f"Ошибка {response.status_code}")
                self.finished.emit(False, error_msg, data)
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Нет соединения с сервером!")
            self.finished.emit(False, "❌ Нет соединения с сервером!", {})
        except requests.exceptions.Timeout:
            print(f"   ⏱️ Таймаут!")
            self.finished.emit(False, f"⏱️ Превышено время ожидания ({self.timeout}с)", {})
        except requests.exceptions.RequestException as e:
            print(f"   ❌ {str(e)}")
            self.finished.emit(False, f"⚠️ Ошибка запроса: {str(e)}", {})
        except Exception as e:
            print(f"   ❌ {str(e)}")
            self.finished.emit(False, f"⚠️ Неизвестная ошибка: {str(e)}", {})


class APIClient:
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager
        self.base_url = Config.API_URL
        self.timeout = Config.API_TIMEOUT
    
    def _log_request(self, method, endpoint, data=None):
        print(f"📤 [{method}] {endpoint}")
        if data:
            log_data = data.copy() if isinstance(data, dict) else data
            if isinstance(log_data, dict) and "password" in log_data:
                log_data["password"] = "***"
            print(f"   📦 {json.dumps(log_data, ensure_ascii=False)}")
    
    def _log_response(self, status_code, endpoint, success, error_msg=None):
        emoji = "✅" if success else "❌"
        print(f"📥 [{status_code}] {endpoint}")
        if success:
            print(f"   ✅ Успешно")
        else:
            print(f"   ❌ {error_msg or 'Ошибка'}")
    
    # ============================================================
    # АУТЕНТИФИКАЦИЯ
    # ============================================================
    
    def register(self, username, password):
        self._log_request("POST", "auth/register", {"username": username, "password": password})
        
        try:
            response = requests.post(
                f"{self.base_url}/auth/register",
                json={"username": username, "password": password},
                timeout=self.timeout
            )
            data = response.json()
            
            print(f"📦 ПАРСИНГ ОТВЕТА: {data}")
            
            if response.status_code == 201 and data.get("success"):
                user_data = data.get("user", {})
                token = data.get("token")
                
                print(f"👤 user_data: {user_data}")
                print(f"🔑 token: {token}")
                
                # ===== ВАЖНО: СОХРАНЯЕМ СЕССИЮ =====
                # Если есть токен - сохраняем с токеном
                if token:
                    self.auth_manager.save_session(token, user_data)
                    print(f"✅ Сессия сохранена с токеном для: {user_data.get('username')}")
                # Если токена нет - создаем локальную сессию
                elif user_data:
                    # Генерируем временный токен для локальной сессии
                    local_token = f"local_{username}_{int(datetime.now().timestamp())}"
                    self.auth_manager.save_session(local_token, user_data)
                    print(f"✅ Локальная сессия создана для: {user_data.get('username')}")
                else:
                    print("⚠️ Нет данных пользователя для сохранения сессии!")
                    return False, "Ошибка: нет данных пользователя", {}
                
                # Проверяем, что сессия сохранилась
                if self.auth_manager.is_authenticated():
                    print(f"✅ Сессия подтверждена для: {self.auth_manager.get_username()}")
                else:
                    print("⚠️ Ошибка: сессия не сохранена!")
                    return False, "Ошибка сохранения сессии", {}
                
                self._log_response(response.status_code, "auth/register", True)
                return True, "Регистрация успешна!", user_data
            else:
                error_msg = data.get("error", {}).get("message", "Неизвестная ошибка")
                self._log_response(response.status_code, "auth/register", False, error_msg)
                return False, error_msg, {}
                
        except requests.exceptions.ConnectionError:
            self._log_response(0, "auth/register", False, "Нет соединения с сервером!")
            return False, "❌ Нет соединения с сервером!", {}
        except requests.exceptions.Timeout:
            self._log_response(0, "auth/register", False, f"Таймаут ({self.timeout}с)")
            return False, f"⏱️ Превышено время ожидания ({self.timeout}с)", {}
        except requests.exceptions.RequestException as e:
            self._log_response(0, "auth/register", False, str(e))
            return False, f"⚠️ Ошибка запроса: {str(e)}", {}
        except Exception as e:
            self._log_response(0, "auth/register", False, str(e))
            return False, f"⚠️ Неизвестная ошибка: {str(e)}", {}
    
    def login(self, username, password):
        self._log_request("POST", "auth/login", {"username": username, "password": password})
        
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={"username": username, "password": password},
                timeout=self.timeout
            )
            data = response.json()
            
            print(f"📦 ПАРСИНГ ОТВЕТА: {data}")
            
            if response.status_code == 200 and data.get("success"):
                token = data.get("token")
                user_data = data.get("user", {})
                
                print(f"👤 user_data: {user_data}")
                print(f"🔑 token: {token}")
                
                # ===== ВАЖНО: СОХРАНЯЕМ СЕССИЮ =====
                if token:
                    self.auth_manager.save_session(token, user_data)
                    print(f"✅ Сессия сохранена с токеном для: {user_data.get('username')}")
                elif user_data:
                    # Если токена нет - создаем локальную сессию
                    local_token = f"local_{username}_{int(datetime.now().timestamp())}"
                    self.auth_manager.save_session(local_token, user_data)
                    print(f"✅ Локальная сессия создана для: {user_data.get('username')}")
                else:
                    print("⚠️ Нет данных пользователя для сохранения сессии!")
                    return False, "Ошибка: нет данных пользователя", {}
                
                # Проверяем, что сессия сохранилась
                if self.auth_manager.is_authenticated():
                    print(f"✅ Сессия подтверждена для: {self.auth_manager.get_username()}")
                else:
                    print("⚠️ Ошибка: сессия не сохранена!")
                    return False, "Ошибка сохранения сессии", {}
                
                self._log_response(response.status_code, "auth/login", True)
                return True, "Вход выполнен!", user_data
            else:
                error_msg = data.get("error", {}).get("message", "Неверный логин или пароль")
                self._log_response(response.status_code, "auth/login", False, error_msg)
                return False, error_msg, {}
                
        except requests.exceptions.ConnectionError:
            self._log_response(0, "auth/login", False, "Нет соединения с сервером!")
            return False, "❌ Нет соединения с сервером!", {}
        except requests.exceptions.Timeout:
            self._log_response(0, "auth/login", False, f"Таймаут ({self.timeout}с)")
            return False, f"⏱️ Превышено время ожидания ({self.timeout}с)", {}
        except requests.exceptions.RequestException as e:
            self._log_response(0, "auth/login", False, str(e))
            return False, f"⚠️ Ошибка запроса: {str(e)}", {}
        except Exception as e:
            self._log_response(0, "auth/login", False, str(e))
            return False, f"⚠️ Неизвестная ошибка: {str(e)}", {}
    
    def get_me(self):
        if not self.auth_manager.is_authenticated():
            return False, "Не авторизован", {}
        
        self._log_request("GET", "auth/me")
        
        try:
            headers = self.auth_manager.get_auth_header()
            response = requests.get(
                f"{self.base_url}/auth/me",
                headers=headers,
                timeout=self.timeout
            )
            data = response.json()
            
            if response.status_code == 200 and data.get("success"):
                user_data = data.get("user", {})
                if self.auth_manager.user:
                    self.auth_manager.user.update(user_data)
                    self.auth_manager.save_session(
                        self.auth_manager.token,
                        self.auth_manager.user
                    )
                self._log_response(response.status_code, "auth/me", True)
                return True, "Данные получены", user_data
            else:
                error_msg = data.get("error", {}).get("message", "Ошибка получения данных")
                self._log_response(response.status_code, "auth/me", False, error_msg)
                return False, error_msg, {}
                
        except requests.exceptions.ConnectionError:
            self._log_response(0, "auth/me", False, "Нет соединения с сервером!")
            return False, "❌ Нет соединения с сервером!", {}
        except requests.exceptions.Timeout:
            self._log_response(0, "auth/me", False, f"Таймаут ({self.timeout}с)")
            return False, f"⏱️ Превышено время ожидания ({self.timeout}с)", {}
        except Exception as e:
            self._log_response(0, "auth/me", False, str(e))
            return False, f"⚠️ Ошибка: {str(e)}", {}
    
    # ============================================================
    # СКИНЫ
    # ============================================================
    
    def get_equipped_skins(self):
        if not self.auth_manager.is_authenticated():
            return False, "Не авторизован", {}
        
        self._log_request("GET", "shop/equipped")
        
        try:
            headers = self.auth_manager.get_auth_header()
            response = requests.get(
                f"{self.base_url}/shop/equipped",
                headers=headers,
                timeout=self.timeout
            )
            data = response.json()
            
            if response.status_code == 200 and data.get("success"):
                equipped = data.get("equipped", {})
                self._log_response(response.status_code, "shop/equipped", True)
                return True, "Активные скины получены", equipped
            else:
                error_msg = data.get("error", {}).get("message", "Ошибка получения активных скинов")
                self._log_response(response.status_code, "shop/equipped", False, error_msg)
                return False, error_msg, {}
                
        except requests.exceptions.ConnectionError:
            self._log_response(0, "shop/equipped", False, "Нет соединения с сервером!")
            return False, "❌ Нет соединения с сервером!", {}
        except requests.exceptions.Timeout:
            self._log_response(0, "shop/equipped", False, f"Таймаут ({self.timeout}с)")
            return False, f"⏱️ Превышено время ожидания ({self.timeout}с)", {}
        except Exception as e:
            self._log_response(0, "shop/equipped", False, str(e))
            return False, f"⚠️ Ошибка: {str(e)}", {}
    
    # ============================================================
    # ИГРА
    # ============================================================
    
    def save_game_result(self, score, games_played=1):
        if not self.auth_manager.is_authenticated():
            return False, "Не авторизован", {}
        
        self._log_request("POST", "game/result", {"score": score, "gamesPlayed": games_played})
        
        try:
            headers = self.auth_manager.get_auth_header()
            response = requests.post(
                f"{self.base_url}/game/result",
                json={"score": int(score), "gamesPlayed": games_played},
                headers=headers,
                timeout=self.timeout
            )
            data = response.json()
            
            if response.status_code == 200 and data.get("success"):
                if self.auth_manager.user and "newBalance" in data:
                    self.auth_manager.user["balance"] = data["newBalance"]
                    self.auth_manager.save_session(
                        self.auth_manager.token,
                        self.auth_manager.user
                    )
                self._log_response(response.status_code, "game/result", True)
                return True, "Результат сохранен!", data
            else:
                error_msg = data.get("error", {}).get("message", "Ошибка сохранения результата")
                self._log_response(response.status_code, "game/result", False, error_msg)
                return False, error_msg, {}
                
        except requests.exceptions.ConnectionError:
            self._log_response(0, "game/result", False, "Нет соединения с сервером!")
            return False, "❌ Нет соединения с сервером!", {}
        except requests.exceptions.Timeout:
            self._log_response(0, "game/result", False, f"Таймаут ({self.timeout}с)")
            return False, f"⏱️ Превышено время ожидания ({self.timeout}с)", {}
        except Exception as e:
            self._log_response(0, "game/result", False, str(e))
            return False, f"⚠️ Ошибка: {str(e)}", {}
    
    # ============================================================
    # ПОЛУЧЕНИЕ ЛУЧШЕГО СЧЕТА
    # ============================================================
    
    def get_best_score(self):
        if not self.auth_manager.is_authenticated():
            return False, "Не авторизован", 0
        
        self._log_request("GET", "best-score")
        
        try:
            headers = self.auth_manager.get_auth_header()
            response = requests.get(
                f"{self.base_url}/best-score",
                headers=headers,
                timeout=self.timeout
            )
            data = response.json()
            
            print(f"📦 ПОЛНЫЙ ОТВЕТ: {data}")
            
            if response.status_code == 200:
                best_score = data.get("bestScore")
                
                if best_score is not None:
                    self._log_response(response.status_code, "best-score", True)
                    return True, "Лучший счет получен", best_score
                
                if data.get("status", False) or data.get("success", False):
                    self._log_response(response.status_code, "best-score", True)
                    return True, "Лучший счет получен", 0
                
                error_msg = data.get("error", {}).get("message", "Ошибка получения лучшего счета")
                self._log_response(response.status_code, "best-score", False, error_msg)
                return False, error_msg, 0
            else:
                error_msg = data.get("error", {}).get("message", f"Ошибка {response.status_code}")
                self._log_response(response.status_code, "best-score", False, error_msg)
                return False, error_msg, 0
                
        except requests.exceptions.ConnectionError:
            self._log_response(0, "best-score", False, "Нет соединения с сервером!")
            return False, "❌ Нет соединения с сервером!", 0
        except requests.exceptions.Timeout:
            self._log_response(0, "best-score", False, f"Таймаут ({self.timeout}с)")
            return False, f"⏱️ Превышено время ожидания ({self.timeout}с)", 0
        except Exception as e:
            self._log_response(0, "best-score", False, str(e))
            return False, f"⚠️ Ошибка: {str(e)}", 0