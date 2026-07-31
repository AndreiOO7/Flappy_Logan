
import requests
import json
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal

from config import Config


class APIThread(QThread):
    """Асинхронный поток для API-запросов"""
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
        print(f"[{self.method}] {self.endpoint}")
        if self.data:
            log_data = self.data.copy() if isinstance(self.data, dict) else self.data
            if isinstance(log_data, dict) and "password" in log_data:
                log_data["password"] = "***"
            print(f"   Данные: {json.dumps(log_data, ensure_ascii=False)}")
        
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
                print(f"   Неизвестный метод: {self.method}")
                self.finished.emit(False, f"Неизвестный метод: {self.method}", {})
                return
            
            if not response.text or not response.text.strip():
                print(f"   Пустой ответ от сервера")
                self.finished.emit(False, "Пустой ответ от сервера", {})
                return
            
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                print(f"   Ошибка парсинга JSON: {e}")
                print(f"   Ответ: {response.text[:200]}...")
                self.finished.emit(False, f"Ошибка парсинга ответа: {str(e)}", {})
                return
            
            print(f"[{response.status_code}] {self.endpoint}")
            
            if response.status_code in [200, 201] and data.get("success", False):
                print(f"   Успешно")
                self.finished.emit(True, "Успешно", data)
            else:
                error_msg = data.get("error", {}).get("message", f"Ошибка {response.status_code}")
                print(f"   Ошибка: {error_msg}")
                self.finished.emit(False, error_msg, data)
                
        except requests.exceptions.ConnectionError:
            print(f"   Нет соединения с сервером")
            self.finished.emit(False, "Нет соединения с сервером", {})
        except requests.exceptions.Timeout:
            print(f"   Таймаут")
            self.finished.emit(False, f"Таймаут ({self.timeout}с)", {})
        except requests.exceptions.RequestException as e:
            print(f"   Ошибка запроса: {str(e)}")
            self.finished.emit(False, f"Ошибка запроса: {str(e)}", {})
        except Exception as e:
            print(f"   Неизвестная ошибка: {str(e)}")
            self.finished.emit(False, f"Неизвестная ошибка: {str(e)}", {})


class APIClient:
    """API-клиент для взаимодействия с сервером"""
    
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager
        self.base_url = Config.API_URL
        self.timeout = Config.API_TIMEOUT
        self._threads = []
    
    def _log_request(self, method, endpoint, data=None):
        print(f"[{method}] {endpoint}")
        if data:
            log_data = data.copy() if isinstance(data, dict) else data
            if isinstance(log_data, dict) and "password" in log_data:
                log_data["password"] = "***"
            print(f"   Данные: {json.dumps(log_data, ensure_ascii=False)}")
    
    def _log_response(self, status_code, endpoint, success, error_msg=None):
        print(f"[{status_code}] {endpoint}")
        if success:
            print(f"   Успешно")
        else:
            print(f"   Ошибка: {error_msg or 'Неизвестная ошибка'}")
    
    def _validate_response(self, data, required_keys=None):
        """Валидирует ответ от сервера"""
        if not isinstance(data, dict):
            return False, "Ответ не является объектом JSON"
        
        if required_keys:
            for key in required_keys:
                if key not in data:
                    return False, f"Отсутствует обязательное поле: {key}"
        
        return True, "OK"
    
    def _is_valid_response(self, response):
        """Проверяет, что ответ валидный и не пустой"""
        if response is None:
            return False, "Ответ отсутствует"
        
        if not response.text or not response.text.strip():
            return False, "Пустой ответ от сервера"
        
        try:
            response.json()
            return True, "OK"
        except json.JSONDecodeError as e:
            return False, f"Ошибка парсинга JSON: {str(e)}"
    
    def _cleanup_thread(self, thread):
        """Очищает поток после завершения"""
        if thread in self._threads:
            self._threads.remove(thread)
        thread.deleteLater()
    
    def register_async(self, username, password, callback):
        """Асинхронная регистрация"""
        thread = APIThread(
            "auth/register", 
            "POST", 
            {"username": username, "password": password},
            timeout=self.timeout
        )
        thread.finished.connect(callback)
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        thread.start()
        self._threads.append(thread)
    
    def login_async(self, username, password, callback):
        """Асинхронный вход"""
        thread = APIThread(
            "auth/login", 
            "POST", 
            {"username": username, "password": password},
            timeout=self.timeout
        )
        thread.finished.connect(callback)
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        thread.start()
        self._threads.append(thread)
    
    def save_game_result_async(self, score, games_played, callback):
        """Асинхронное сохранение результата"""
        if not self.auth_manager.is_authenticated():
            callback(False, "Не авторизован", {})
            return
        
        thread = APIThread(
            "game/result",
            "POST",
            {"score": int(score), "gamesPlayed": games_played},
            token=self.auth_manager.token,
            timeout=self.timeout
        )
        thread.finished.connect(callback)
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        thread.start()
        self._threads.append(thread)
    
    def register(self, username, password):
        """Синхронная регистрация (устаревший метод)"""
        self._log_request("POST", "auth/register", {"username": username, "password": password})
        
        try:
            response = requests.post(
                f"{self.base_url}/auth/register",
                json={"username": username, "password": password},
                timeout=self.timeout
            )
            
            is_valid, error_msg = self._is_valid_response(response)
            if not is_valid:
                self._log_response(0, "auth/register", False, error_msg)
                return False, error_msg, {}
            
            data = response.json()
            
            is_valid, error_msg = self._validate_response(data, ["success"])
            if not is_valid:
                self._log_response(response.status_code, "auth/register", False, error_msg)
                return False, error_msg, {}
            
            if response.status_code == 201 and data.get("success"):
                user_data = data.get("user", {})
                token = data.get("token")
                
                if not user_data:
                    return False, "Нет данных пользователя", {}
                
                if token:
                    self.auth_manager.save_session(token, user_data)
                else:
                    local_token = f"local_{username}_{int(datetime.now().timestamp())}"
                    self.auth_manager.save_session(local_token, user_data)
                
                self._log_response(response.status_code, "auth/register", True)
                return True, "Регистрация успешна", user_data
            else:
                error_msg = data.get("error", {}).get("message", "Неизвестная ошибка")
                self._log_response(response.status_code, "auth/register", False, error_msg)
                return False, error_msg, {}
                
        except requests.exceptions.ConnectionError:
            self._log_response(0, "auth/register", False, "Нет соединения с сервером")
            return False, "Нет соединения с сервером", {}
        except requests.exceptions.Timeout:
            self._log_response(0, "auth/register", False, f"Таймаут ({self.timeout}с)")
            return False, f"Таймаут ({self.timeout}с)", {}
        except requests.exceptions.RequestException as e:
            self._log_response(0, "auth/register", False, str(e))
            return False, f"Ошибка запроса: {str(e)}", {}
        except Exception as e:
            self._log_response(0, "auth/register", False, str(e))
            return False, f"Неизвестная ошибка: {str(e)}", {}
    
    def login(self, username, password):
        """Синхронный вход (устаревший метод)"""
        self._log_request("POST", "auth/login", {"username": username, "password": password})
        
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={"username": username, "password": password},
                timeout=self.timeout
            )
            
            is_valid, error_msg = self._is_valid_response(response)
            if not is_valid:
                self._log_response(0, "auth/login", False, error_msg)
                return False, error_msg, {}
            
            data = response.json()
            
            is_valid, error_msg = self._validate_response(data, ["success"])
            if not is_valid:
                self._log_response(response.status_code, "auth/login", False, error_msg)
                return False, error_msg, {}
            
            if response.status_code == 200 and data.get("success"):
                token = data.get("token")
                user_data = data.get("user", {})
                
                if not user_data:
                    return False, "Нет данных пользователя", {}
                
                if not token:
                    return False, "Сервер не вернул токен", {}
                
                self.auth_manager.save_session(token, user_data)
                
                self._log_response(response.status_code, "auth/login", True)
                return True, "Вход выполнен", user_data
            else:
                error_msg = data.get("error", {}).get("message", "Неверный логин или пароль")
                self._log_response(response.status_code, "auth/login", False, error_msg)
                return False, error_msg, {}
                
        except requests.exceptions.ConnectionError:
            self._log_response(0, "auth/login", False, "Нет соединения с сервером")
            return False, "Нет соединения с сервером", {}
        except requests.exceptions.Timeout:
            self._log_response(0, "auth/login", False, f"Таймаут ({self.timeout}с)")
            return False, f"Таймаут ({self.timeout}с)", {}
        except Exception as e:
            self._log_response(0, "auth/login", False, str(e))
            return False, f"Ошибка: {str(e)}", {}
    
    def get_equipped_skins(self):
        """Получение активных скинов (синхронно)"""
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
            
            is_valid, error_msg = self._is_valid_response(response)
            if not is_valid:
                self._log_response(0, "shop/equipped", False, error_msg)
                return False, error_msg, {}
            
            data = response.json()
            
            is_valid, error_msg = self._validate_response(data, ["success"])
            if not is_valid:
                self._log_response(response.status_code, "shop/equipped", False, error_msg)
                return False, error_msg, {}
            
            if response.status_code == 200 and data.get("success"):
                equipped = data.get("equipped", {})
                self._log_response(response.status_code, "shop/equipped", True)
                return True, "Скины загружены", equipped
            else:
                error_msg = data.get("error", {}).get("message", "Ошибка загрузки скинов")
                self._log_response(response.status_code, "shop/equipped", False, error_msg)
                return False, error_msg, {}
                
        except requests.exceptions.ConnectionError:
            self._log_response(0, "shop/equipped", False, "Нет соединения с сервером")
            return False, "Нет соединения с сервером", {}
        except requests.exceptions.Timeout:
            self._log_response(0, "shop/equipped", False, f"Таймаут ({self.timeout}с)")
            return False, f"Таймаут ({self.timeout}с)", {}
        except Exception as e:
            self._log_response(0, "shop/equipped", False, str(e))
            return False, f"Ошибка: {str(e)}", {}
    
    def save_game_result(self, score, games_played=1):
        """Синхронное сохранение результата (устаревший метод)"""
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
            
            is_valid, error_msg = self._is_valid_response(response)
            if not is_valid:
                self._log_response(0, "game/result", False, error_msg)
                return False, error_msg, {}
            
            data = response.json()
            
            is_valid, error_msg = self._validate_response(data, ["success"])
            if not is_valid:
                self._log_response(response.status_code, "game/result", False, error_msg)
                return False, error_msg, {}
            
            if response.status_code == 200 and data.get("success"):
                if self.auth_manager.user and "newBalance" in data:
                    self.auth_manager.user["balance"] = data["newBalance"]
                    self.auth_manager.save_session(
                        self.auth_manager.token,
                        self.auth_manager.user
                    )
                self._log_response(response.status_code, "game/result", True)
                return True, "Результат сохранён", data
            else:
                error_msg = data.get("error", {}).get("message", "Ошибка сохранения результата")
                self._log_response(response.status_code, "game/result", False, error_msg)
                return False, error_msg, {}
                
        except requests.exceptions.ConnectionError:
            self._log_response(0, "game/result", False, "Нет соединения с сервером")
            return False, "Нет соединения с сервером", {}
        except requests.exceptions.Timeout:
            self._log_response(0, "game/result", False, f"Таймаут ({self.timeout}с)")
            return False, f"Таймаут ({self.timeout}с)", {}
        except Exception as e:
            self._log_response(0, "game/result", False, str(e))
            return False, f"Ошибка: {str(e)}", {}
    
    def get_best_score(self):
        """Получение лучшего счета (синхронно)"""
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
            
            is_valid, error_msg = self._is_valid_response(response)
            if not is_valid:
                self._log_response(0, "best-score", False, error_msg)
                return False, error_msg, 0
            
            data = response.json()
            
            is_valid, error_msg = self._validate_response(data)
            if not is_valid:
                self._log_response(response.status_code, "best-score", False, error_msg)
                return False, error_msg, 0
            
            if response.status_code == 200:
                best_score = data.get("bestScore")
                
                if best_score is not None and isinstance(best_score, (int, float)):
                    self._log_response(response.status_code, "best-score", True)
                    return True, "Лучший счёт получен", int(best_score)
                
                if data.get("status", False) or data.get("success", False):
                    self._log_response(response.status_code, "best-score", True)
                    return True, "Лучший счёт получен", 0
                
                error_msg = data.get("error", {}).get("message", "Ошибка получения лучшего счёта")
                self._log_response(response.status_code, "best-score", False, error_msg)
                return False, error_msg, 0
            else:
                error_msg = data.get("error", {}).get("message", f"Ошибка {response.status_code}")
                self._log_response(response.status_code, "best-score", False, error_msg)
                return False, error_msg, 0
                
        except requests.exceptions.ConnectionError:
            self._log_response(0, "best-score", False, "Нет соединения с сервером")
            return False, "Нет соединения с сервером", 0
        except requests.exceptions.Timeout:
            self._log_response(0, "best-score", False, f"Таймаут ({self.timeout}с)")
            return False, f"Таймаут ({self.timeout}с)", 0
        except Exception as e:
            self._log_response(0, "best-score", False, str(e))
            return False, f"Ошибка: {str(e)}", 0
