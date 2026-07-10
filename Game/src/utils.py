# src/utils.py
"""
Утилиты и константы для игры Flappy Logan
"""

import os
import sys
from pathlib import Path
from PyQt5.QtGui import QPixmap

from config import Config


# ============================================================
# КОНСТАНТЫ ИГРЫ
# ============================================================

GAME_WIDTH = Config.GAME_WIDTH
GAME_HEIGHT = Config.GAME_HEIGHT

bird_x = int(GAME_WIDTH / 8)
bird_y = int(GAME_HEIGHT / 2)
bird_width = Config.BIRD_WIDTH
bird_height = Config.BIRD_HEIGHT

pipe_x = GAME_WIDTH
pipe_y = 0
pipe_width = Config.PIPE_WIDTH
pipe_height = Config.PIPE_HEIGHT


# ============================================================
# ФУНКЦИИ
# ============================================================

def center_window(window):
    """Центрирует окно на экране"""
    screen = window.screen().availableGeometry()
    x = (screen.width() - window.width()) // 2
    y = (screen.height() - window.height()) // 2
    window.move(x, y)


def load_asset(category, skin_id, width=None, height=None):
    """Загружает изображение скина из папки assets"""
    # Для .exe и для разработки
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Config.BASE_DIR
    
    filepath = base_path / "assets" / category / f"{skin_id}.png"
    
    if not filepath.exists():
        return None
    
    try:
        pixmap = QPixmap(str(filepath))
        if width and height:
            pixmap = pixmap.scaled(width, height)
        return pixmap
    except Exception:
        return None


def ensure_assets_directory():
    """Создает папку assets и подпапки если их нет"""
    Config.ensure_directories()
    return True