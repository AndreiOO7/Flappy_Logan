# main.py
"""
Flappy Logan - Главный файл запуска
"""

import sys
import os

# Добавляем папку src в путь для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from config import Config
from registration import RegistrationWindow
from auth_manager import AuthManager
from network import APIClient
from game import FlappyBird


def main():
    print(f"🚀 Запуск Flappy Logan v{Config.APP_VERSION}")
    print(f"📡 API URL: {Config.API_URL}")
    print(f"⏱️  Таймаут: {Config.API_TIMEOUT}с")
    print("═" * 50)
    
    Config.ensure_all_files()
    
    app = QApplication(sys.argv)
    app.setApplicationName("Флаппи Логан")
    
    try:
        app.setWindowIcon(QIcon("assets/icon.ico"))
    except:
        pass
    
    auth_manager = AuthManager()
    
    if auth_manager.is_authenticated():
        username = auth_manager.get_username()
        if username and username != "Guest":
            print(f"✅ Сессия найдена! Пользователь: {username}")
            
            api_client = APIClient(auth_manager)
            success, _, best_score = api_client.get_best_score()
            if success:
                auth_manager.update_user_data({"bestScore": best_score})
                print(f"🏆 Лучший счет загружен: {best_score}")
            else:
                print(f"⚠️ Не удалось загрузить лучший счет")
            
            print("🎮 Открываю игру...")
            game_window = FlappyBird(username)
            game_window.show()
        else:
            print("⚠️ Невалидная сессия, очищаю...")
            auth_manager.clear_session()
            print("📝 Открываю окно регистрации...")
            registration_window = RegistrationWindow()
            registration_window.show()
    else:
        print("❌ Сессия не найдена")
        print("📝 Открываю окно регистрации...")
        registration_window = RegistrationWindow()
        registration_window.show()
    
    print("✅ Приложение запущено!")
    print("═" * 50)
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()