
import sys
from pathlib import Path
from PyQt5.QtGui import QPixmap, QColor, QPainter, QPen
from PyQt5.QtCore import Qt, QUrl

from config import Config


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


def get_base_path():
    """Возвращает базовый путь для ресурсов. Для .exe — sys._MEIPASS"""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    else:
        return Config.BASE_DIR


def get_resource_path(relative_path):
    """Возвращает полный путь к ресурсу"""
    return get_base_path() / relative_path


def get_asset_path(category, filename):
    """Возвращает путь к файлу ассета"""
    return get_resource_path(f"assets/{category}/{filename}")


def center_window(window):
    """Центрирует окно на экране"""
    screen = window.screen().availableGeometry()
    x = (screen.width() - window.width()) // 2
    y = (screen.height() - window.height()) // 2
    window.move(x, y)


def create_fallback_pixmap(category, width=None, height=None):
    """Создаёт заглушку для отсутствующего скина"""
    if width is None:
        width = 100
    if height is None:
        height = 100
    
    pixmap = QPixmap(width, height)
    
    colors = {
        "birds": QColor(255, 215, 0),
        "pipes": QColor(0, 200, 0),
        "pipes_top": QColor(0, 200, 0),
        "pipes_bottom": QColor(0, 200, 0),
        "backgrounds": QColor(135, 206, 235)
    }
    
    color = colors.get(category, QColor(128, 128, 128))
    pixmap.fill(color)
    
    painter = QPainter(pixmap)
    painter.setPen(QPen(Qt.black, 2))
    painter.drawRect(0, 0, width - 1, height - 1)
    painter.end()
    
    return pixmap


def load_asset(category, skin_id, width=None, height=None):
    """Загружает изображение скина с обработкой ошибок"""
    filepath = get_asset_path(category, f"{skin_id}.png")
    
    if not filepath.exists():
        print(f"Файл не найден: {filepath}")
        return create_fallback_pixmap(category, width, height)
    
    try:
        pixmap = QPixmap(str(filepath))
        if pixmap.isNull():
            print(f"Не удалось загрузить: {filepath}")
            return create_fallback_pixmap(category, width, height)
        
        if width and height:
            pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return pixmap
    except Exception as e:
        print(f"Ошибка загрузки {skin_id}: {e}")
        return create_fallback_pixmap(category, width, height)


def load_music_file(filename="track.mp3"):
    """Загружает музыкальный файл с правильным путём"""
    music_path = get_asset_path("music", filename)
    
    if not music_path.exists():
        print(f"Музыкальный файл не найден: {music_path}")
        return None
    
    print(f"Музыка найдена: {music_path}")
    return str(music_path)


def get_audio_url(filename="track.mp3"):
    """Возвращает QUrl для музыкального файла"""
    music_path = load_music_file(filename)
    if music_path is None:
        return None
    
    return QUrl.fromLocalFile(music_path)


def debug_resources():
    """Выводит информацию о доступных ресурсах (для отладки)"""
    print("=" * 50)
    print("ДИАГНОСТИКА РЕСУРСОВ")
    print(f"  frozen: {getattr(sys, 'frozen', False)}")
    print(f"  base_path: {get_base_path()}")
    
    music_path = get_asset_path("music", "track.mp3")
    print(f"  music_path: {music_path}")
    print(f"  exists: {music_path.exists()}")
    
    assets_path = get_base_path() / "assets"
    print(f"  assets_path: {assets_path}")
    print(f"  exists: {assets_path.exists()}")
    
    if assets_path.exists():
        print("  Содержимое assets:")
        for item in assets_path.iterdir():
            print(f"    - {item.name}")
            if item.is_dir():
                for subitem in item.iterdir():
                    print(f"      - {subitem.name}")
    
    print("=" * 50)
