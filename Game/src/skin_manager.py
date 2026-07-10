# src/skin_manager.py
"""
Менеджер скинов для игры Flappy Logan
Управляет загрузкой, кэшированием и синхронизацией скинов
"""

import os
import json
from PyQt5.QtGui import QPixmap

from config import Config
from utils import load_asset


class SkinManager:
    def __init__(self, auth_manager, api_client):
        self.auth_manager = auth_manager
        self.api_client = api_client
        
        self._cache = {
            "birds": {},
            "pipes": {},
            "backgrounds": {}
        }
        
        self.equipped = {
            "birds": Config.DEFAULT_SKINS.get("birds", "bird-default"),
            "pipes_top": Config.DEFAULT_SKINS.get("pipes_top", "pipe-top-default"),
            "pipes_bottom": Config.DEFAULT_SKINS.get("pipes_bottom", "pipe-bottom-default"),
            "backgrounds": Config.DEFAULT_SKINS.get("backgrounds", "bg-default")
        }
        
        self.load_equipped_from_cache()
    
    # ============================================================
    # ЗАГРУЗКА ИЗОБРАЖЕНИЙ
    # ============================================================
    
    def load_skin_image(self, category, skin_id, width=None, height=None):
        """Загружает изображение скина с кэшированием"""
        cache_key = f"{skin_id}_{width}_{height}" if width and height else skin_id
        
        if category in self._cache and skin_id in self._cache.get(category, {}):
            cached = self._cache[category].get(cache_key)
            if cached is not None:
                return cached
        
        load_category = "pipes" if category in ["pipes_top", "pipes_bottom"] else category
        
        pixmap = load_asset(load_category, skin_id, width, height)
        
        if pixmap is None:
            from PyQt5.QtGui import QColor
            pixmap = QPixmap(width or 100, height or 100)
            colors = {
                "birds": QColor(255, 255, 0),
                "pipes": QColor(0, 255, 0),
                "pipes_top": QColor(0, 255, 0),
                "pipes_bottom": QColor(0, 255, 0),
                "backgrounds": QColor(135, 206, 235)
            }
            pixmap.fill(colors.get(category, QColor(128, 128, 128)))
        
        if category not in self._cache:
            self._cache[category] = {}
        self._cache[category][cache_key] = pixmap
        
        return pixmap
    
    def load_bird(self, skin_id, width=None, height=None):
        return self.load_skin_image("birds", skin_id, width, height)
    
    def load_pipe_top(self, skin_id, width=None, height=None):
        return self.load_skin_image("pipes_top", skin_id, width, height)
    
    def load_pipe_bottom(self, skin_id, width=None, height=None):
        return self.load_skin_image("pipes_bottom", skin_id, width, height)
    
    def load_background(self, skin_id, width=None, height=None):
        return self.load_skin_image("backgrounds", skin_id, width, height)
    
    def clear_cache(self):
        self._cache = {
            "birds": {},
            "pipes": {},
            "pipes_top": {},
            "pipes_bottom": {},
            "backgrounds": {}
        }
    
    # ============================================================
    # УПРАВЛЕНИЕ АКТИВНЫМИ СКИНАМИ
    # ============================================================
    
    def get_equipped_skins(self):
        return self.equipped.copy()
    
    def reset_equipped(self):
        self.equipped = {
            "birds": Config.DEFAULT_SKINS.get("birds", "bird-default"),
            "pipes_top": Config.DEFAULT_SKINS.get("pipes_top", "pipe-top-default"),
            "pipes_bottom": Config.DEFAULT_SKINS.get("pipes_bottom", "pipe-bottom-default"),
            "backgrounds": Config.DEFAULT_SKINS.get("backgrounds", "bg-default")
        }
        self.save_equipped_to_cache()
    
    # ============================================================
    # КЭШИРОВАНИЕ
    # ============================================================
    
    def save_equipped_to_cache(self):
        try:
            with open(Config.EQUIPPED_SKINS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.equipped, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"⚠️ Ошибка сохранения скинов: {e}")
            return False
    
    def load_equipped_from_cache(self):
        try:
            if os.path.exists(Config.EQUIPPED_SKINS_FILE):
                if os.path.getsize(Config.EQUIPPED_SKINS_FILE) == 0:
                    self.save_equipped_to_cache()
                    return True
                
                with open(Config.EQUIPPED_SKINS_FILE, 'r', encoding='utf-8-sig') as f:
                    content = f.read().strip()
                    if not content:
                        self.save_equipped_to_cache()
                        return True
                    
                    equipped = json.loads(content)
                    
                    categories = ["birds", "pipes_top", "pipes_bottom", "backgrounds"]
                    for category in categories:
                        if category in equipped:
                            self.equipped[category] = equipped[category]
                    return True
        except json.JSONDecodeError as e:
            print(f"⚠️ Ошибка парсинга equipped_skins.json: {e}")
            self.save_equipped_to_cache()
            return True
        except Exception as e:
            print(f"⚠️ Ошибка загрузки скинов: {e}")
            self.save_equipped_to_cache()
            return False
        return False
    
    # ============================================================
    # СИНХРОНИЗАЦИЯ С СЕРВЕРОМ
    # ============================================================
    
    def sync_with_server(self):
        """Синхронизирует активные скины с сервером"""
        # ===== ВАЖНО: ПРОВЕРЯЕМ АВТОРИЗАЦИЮ =====
        if not self.auth_manager.is_authenticated():
            print("⚠️ Пользователь не авторизован, пропускаем синхронизацию скинов")
            return False
        
        print("🔄 Синхронизация скинов с сервером...")
        
        equip_success, message, equipped = self.api_client.get_equipped_skins()
        if equip_success:
            # Преобразуем формат pipes в pipes_top и pipes_bottom
            if "pipes" in equipped and "pipes_top" not in equipped:
                pipe_skin = equipped["pipes"]
                equipped["pipes_top"] = f"{pipe_skin}-top"
                equipped["pipes_bottom"] = f"{pipe_skin}-bottom"
            
            # Обновляем активные скины
            categories = ["birds", "pipes_top", "pipes_bottom", "backgrounds"]
            for category in categories:
                if category in equipped and equipped[category]:
                    self.equipped[category] = equipped[category]
                    print(f"   ✅ {category}: {equipped[category]}")
            
            self.save_equipped_to_cache()
            return True
        else:
            print(f"⚠️ Не удалось загрузить скины: {message}")
            return False
    
    def load_equipped_skins(self):
        """Загружает активные скины из кэша и синхронизирует с сервером"""
        self.load_equipped_from_cache()
        
        # ===== ВАЖНО: СИНХРОНИЗИРУЕМ ТОЛЬКО ЕСЛИ АВТОРИЗОВАН =====
        if self.auth_manager.is_authenticated():
            print("🔄 Синхронизация скинов с сервером...")
            self.sync_with_server()
        else:
            print("⚠️ Не авторизован, используем локальные скины")
        
        return self.get_equipped_skins()