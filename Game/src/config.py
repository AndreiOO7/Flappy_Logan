# src/config.py
"""
Конфигурация приложения Flappy Logan
"""

import os
import json
from pathlib import Path


class Config:
    # ============================================================
    # БАЗОВЫЕ НАСТРОЙКИ
    # ============================================================
    
    APP_NAME = "Флаппи Логан"
    APP_VERSION = "2.0.0"
    
    # ============================================================
    # ССЫЛКИ
    # ============================================================
    
    WEBSITE_URL = "https://proactive-reprieve-production-f162.up.railway.app"
    
    # ============================================================
    # API НАСТРОЙКИ
    # ============================================================
    
    API_URL = os.getenv("FLAPPY_API_URL", "https://flappylogan-production.up.railway.app/api")
    API_TIMEOUT = int(os.getenv("FLAPPY_API_TIMEOUT", "10"))
    
    # ============================================================
    # ПУТИ К ФАЙЛАМ
    # ============================================================
    
    BASE_DIR = Path(__file__).parent.parent.absolute()
    ASSETS_DIR = BASE_DIR / "assets"
    DATA_DIR = BASE_DIR / "data"
    
    SESSION_FILE = DATA_DIR / "session.json"
    SETTINGS_FILE = DATA_DIR / "settings.json"
    EQUIPPED_SKINS_FILE = DATA_DIR / "equipped_skins.json"
    
    # ============================================================
    # НАСТРОЙКИ ИГРЫ
    # ============================================================
    
    GAME_WIDTH = 600
    GAME_HEIGHT = 1000
    BIRD_WIDTH = 56
    BIRD_HEIGHT = 40
    PIPE_WIDTH = 100
    PIPE_HEIGHT = 800
    GAME_FPS = 60
    
    # ============================================================
    # НАСТРОЙКИ СЛОЖНОСТИ
    # ============================================================
    
    DEFAULT_DIFFICULTY = "normal"
    
    DIFFICULTY_SETTINGS = {
        "easy": {
            "gravity": 0.4,
            "jump_power": -10,
            "pipe_speed": -2,
            "pipe_interval": 1800
        },
        "normal": {
            "gravity": 0.6,
            "jump_power": -9,
            "pipe_speed": -3,
            "pipe_interval": 1500
        },
        "hard": {
            "gravity": 0.8,
            "jump_power": -7,
            "pipe_speed": -5,
            "pipe_interval": 1200
        }
    }
    
    # ============================================================
    # НАСТРОЙКИ СКИНОВ
    # ============================================================
    
    DEFAULT_SKINS = {
        "birds": "bird-default",
        "pipes_top": "pipe-default-top",
        "pipes_bottom": "pipe-default-top",
        "backgrounds": "bg-default"
    }
    
    # ============================================================
    # НАСТРОЙКИ ПРОФИЛЯ
    # ============================================================
    
    USERNAME_MIN_LENGTH = 3
    USERNAME_MAX_LENGTH = 20
    PASSWORD_MIN_LENGTH = 4
    USERNAME_PATTERN = r'^[a-zA-Z0-9_]+$'

    DEFAULT_SETTINGS = {
        "gravity": 0.6,
        "jump_power": -9,
        "pipe_speed": -3,
        "pipe_interval": 1500,
        "sound_enabled": True,
        "difficulty": "normal",
        "volume": 80
    }
    
    # ============================================================
    # МЕТОДЫ
    # ============================================================
    
    @classmethod
    def ensure_directories(cls):
        """Создает все необходимые директории"""
        directories = [
            cls.ASSETS_DIR,
            cls.ASSETS_DIR / "birds",
            cls.ASSETS_DIR / "pipes",
            cls.ASSETS_DIR / "backgrounds",
            cls.ASSETS_DIR / "music",
            cls.DATA_DIR,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"✅ Папка: {directory.name}")
        return True
    
    @classmethod
    def ensure_all_files(cls):
        """Создает все необходимые файлы с дефолтным содержимым"""
        cls.ensure_directories()
        
        files = [
            (cls.SESSION_FILE, {}),
            (cls.SETTINGS_FILE, cls.DEFAULT_SETTINGS),
            (cls.EQUIPPED_SKINS_FILE, cls.DEFAULT_SKINS)
        ]
        
        for filepath, default_content in files:
            if not filepath.exists():
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(default_content, f, ensure_ascii=False, indent=2)
                    print(f"✅ Создан файл: {filepath.name}")
                except Exception as e:
                    print(f"⚠️ Ошибка создания файла {filepath}: {e}")
        
        return True