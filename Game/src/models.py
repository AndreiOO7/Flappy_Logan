# src/models.py
"""
Модели данных для игры Flappy Logan
"""

import json
from PyQt5.QtCore import QRect

from utils import bird_x, bird_y, bird_width, bird_height, pipe_x, pipe_y, pipe_width, pipe_height


class Bird:
    """Класс птицы"""
    
    def __init__(self, img):
        self.x = bird_x
        self.y = bird_y
        self.width = bird_width
        self.height = bird_height
        self.img = img
        self.rotation = 0

    def get_rect(self):
        return QRect(self.x, self.y, self.width, self.height)
    
    def update_rotation(self, velocity_y):
        if velocity_y < 0:
            self.rotation = max(self.rotation - 3, -30)
        else:
            self.rotation = min(self.rotation + 3, 60)
    
    def reset(self):
        self.x = bird_x
        self.y = bird_y
        self.rotation = 0


class Pipe:
    """Класс трубы"""
    
    def __init__(self, img):
        self.x = pipe_x
        self.y = pipe_y
        self.width = pipe_width
        self.height = pipe_height
        self.img = img
        self.passed = False

    def get_rect(self):
        return QRect(self.x, self.y, self.width, self.height)
    
    def reset(self):
        self.x = pipe_x
        self.y = pipe_y
        self.passed = False


class Settings:
    """Класс настроек игры"""
    
    DEFAULT_SETTINGS = {
        "gravity": 0.6,
        "jump_power": -9,
        "pipe_speed": -3,
        "pipe_interval": 1500,
        "sound_enabled": True,
        "difficulty": "normal",
        "volume": 80
    }
    
    def __init__(self):
        for key, value in self.DEFAULT_SETTINGS.items():
            setattr(self, key, value)
        self.load_settings()
    
    def load_settings(self):
        from config import Config
        try:
            with open(Config.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for key in self.DEFAULT_SETTINGS:
                    if key in data:
                        setattr(self, key, data[key])
        except:
            pass
    
    def save_settings(self):
        from config import Config
        try:
            with open(Config.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump({k: getattr(self, k) for k in self.DEFAULT_SETTINGS}, f, ensure_ascii=False, indent=4)
        except:
            pass
    
    def get_difficulty_params(self):
        difficulties = {
            "easy": {"gravity": 0.4, "jump_power": -10, "pipe_speed": -2, "pipe_interval": 1800},
            "normal": {"gravity": 0.6, "jump_power": -9, "pipe_speed": -3, "pipe_interval": 1500},
            "hard": {"gravity": 0.8, "jump_power": -7, "pipe_speed": -5, "pipe_interval": 1200}
        }
        return difficulties.get(self.difficulty, difficulties["normal"])