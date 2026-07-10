# game.py
import random
from PyQt5.QtWidgets import (QWidget, QLabel, QPushButton, QVBoxLayout, 
                             QHBoxLayout, QFrame, QComboBox, QSlider, QMessageBox, QApplication)
from PyQt5.QtCore import Qt, QTimer, QUrl
from PyQt5.QtGui import QPixmap, QPainter, QFont, QPen, QColor
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

from utils import GAME_WIDTH, GAME_HEIGHT, bird_x, bird_y, bird_width, bird_height
from utils import pipe_x, pipe_y, pipe_width, pipe_height, center_window, load_asset
from models import Bird, Pipe, Settings
from dialogs import CustomDialog
from auth_manager import AuthManager
from network import APIClient
from skin_manager import SkinManager
from hyperlink import Hyperlink
from config import Config


class FlappyBird(QWidget):
    def __init__(self, username, registration_window=None, auth_manager=None):
        super().__init__()
        self.username = username
        self.registration_window = registration_window
        
        # Используем переданный auth_manager или создаём новый
        if auth_manager:
            self.auth_manager = auth_manager
        else:
            self.auth_manager = AuthManager()
        
        # ===== ВАЖНО: ПРИНУДИТЕЛЬНО ЗАГРУЖАЕМ СЕССИЮ =====
        self.auth_manager.refresh_session()
        
        # Проверяем авторизацию
        if self.auth_manager.is_authenticated():
            print(f"✅ Игра запущена для пользователя: {self.auth_manager.get_username()}")
            print(f"   Баланс: {self.auth_manager.get_balance()}")
            print(f"   Лучший счет: {self.auth_manager.get_best_score()}")
        else:
            print("⚠️ Пользователь не авторизован!")
        
        self.api_client = APIClient(self.auth_manager)
        self.skin_manager = SkinManager(self.auth_manager, self.api_client)
        
        self.player = QMediaPlayer()
        self.music_playing = False
        self.load_music()
        
        self.equipped_skins = self.skin_manager.load_equipped_skins()
        
        self.settings = Settings()
        self.menu_visible = False
        self.game_started = False
        self.is_paused = False
        self.show_main_menu = True
        self.is_settings_from_menu = False
        
        self.best_score = 0
        self.balance = 0
        self.total_score = 0
        self.games_played = 0
        self.load_user_data()

        self.load_game_assets()

        self.bird = Bird(self.bird_image)
        self.pipes = []
        self.velocity_x = self.settings.pipe_speed
        self.velocity_y = 0
        self.gravity = self.settings.gravity
        self.score = 0
        self.game_over = False
        self.score_saved = False

        self.setFixedSize(GAME_WIDTH, GAME_HEIGHT)
        self.setWindowTitle("Флаппи Логан")
        self.setStyleSheet("background-color: black;")
        center_window(self)

        self.game_timer = QTimer()
        self.game_timer.timeout.connect(self.game_loop)
        self.game_timer.start(1000 // 60)

        self.pipe_timer = QTimer()
        self.pipe_timer.timeout.connect(self.create_pipes)

        self.main_menu_panel = QFrame(self)
        self.main_menu_panel.setGeometry(0, 0, GAME_WIDTH, GAME_HEIGHT)
        self.main_menu_panel.setStyleSheet("""
            QFrame {
                background-color: #000000;
            }
            QLabel {
                color: #e0e0e0;
                font-size: 15px;
            }
        """)
        self.init_main_menu()
        
        self.overlay = QFrame(self)
        self.overlay.setGeometry(0, 0, GAME_WIDTH, GAME_HEIGHT)
        self.overlay.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 150);
            }
        """)
        self.overlay.hide()
        
        self.menu_panel = QFrame(self)
        self.menu_panel.setGeometry(50, 120, 500, 560)
        self.menu_panel.setStyleSheet("""
            QFrame {
                background-color: #000000;
                border: 2px solid #0fcf8a;
                border-radius: 16px;
            }
            QLabel {
                color: #e0e0e0;
                font-size: 15px;
            }
            QPushButton {
                background-color: #0fcf8a;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #0dbd7e;
            }
            QPushButton:pressed {
                background-color: #0caa70;
            }
            QPushButton#close_btn {
                background-color: transparent;
                color: #ff4444;
                border: 2px solid #ff4444;
                font-size: 14px;
                padding: 8px 20px;
            }
            QPushButton#close_btn:hover {
                background-color: rgba(255, 68, 68, 0.2);
            }
            QPushButton#menu_btn {
                background-color: transparent;
                color: #888888;
                border: 1px solid #333333;
                font-size: 14px;
                padding: 8px 20px;
            }
            QPushButton#menu_btn:hover {
                color: #e0e0e0;
                border-color: #555555;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: #333333;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #0fcf8a;
                border: none;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #0dbd7e;
            }
            QSlider::sub-page:horizontal {
                background: #0fcf8a;
                border-radius: 2px;
            }
            QComboBox {
                background-color: #1a1a1a;
                color: #e0e0e0;
                border: 2px solid #2a2a2a;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 15px;
                font-weight: 600;
                min-width: 120px;
            }
            QComboBox:hover {
                border-color: #0fcf8a;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid #888888;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1a1a;
                color: #e0e0e0;
                border: 2px solid #2a2a2a;
                selection-background-color: #0fcf8a;
                selection-color: white;
                font-weight: 600;
            }
            QLabel#value_label {
                color: #0fcf8a;
                font-weight: bold;
                min-width: 40px;
            }
        """)
        self.menu_panel.hide()
        
        self.go_restart_btn = QPushButton("Restart", self)
        self.go_restart_btn.setFixedSize(100, 35)
        self.go_restart_btn.setStyleSheet("""
            QPushButton {
                background-color: #0fcf8a;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #0dbd7e;
            }
        """)
        self.go_restart_btn.hide()
        self.go_restart_btn.clicked.connect(self.restart_game)
        
        self.go_menu_btn = QPushButton("Menu", self)
        self.go_menu_btn.setFixedSize(100, 35)
        self.go_menu_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #e0e0e0;
                border: 2px solid #555555;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.05);
                border-color: #0fcf8a;
                color: #ffffff;
            }
        """)
        self.go_menu_btn.hide()
        self.go_menu_btn.clicked.connect(self.go_to_main_menu)
        
        self.init_pause_menu()

        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        self.show()
        
        # ===== НЕ ЗАПУСКАЕМ МУЗЫКУ СРАЗУ =====
        # self.start_music()  # <-- УБИРАЕМ ЭТУ СТРОКУ

    # ============================================================
    # МУЗЫКА
    # ============================================================
    
    def load_music(self):
        music_path = "assets/music/track.mp3"
        try:
            url = QUrl.fromLocalFile(music_path)
            content = QMediaContent(url)
            self.player.setMedia(content)
            volume = self.settings.volume if hasattr(self.settings, 'volume') else 80
            self.player.setVolume(volume)
            print(f"🎵 Музыка загружена, громкость: {volume}%")
        except Exception as e:
            print(f"⚠️ Ошибка загрузки музыки: {e}")
    
    def start_music(self):
        """Запускает музыку только если игра активна"""
        if not self.music_playing and self.settings.sound_enabled and self.game_started and not self.game_over and not self.show_main_menu:
            try:
                self.player.play()
                self.music_playing = True
                print("🎵 Музыка запущена")
            except Exception as e:
                print(f"⚠️ Ошибка запуска музыки: {e}")
    
    def stop_music(self):
        try:
            self.player.stop()
            self.music_playing = False
            print("🎵 Музыка остановлена")
        except Exception as e:
            print(f"⚠️ Ошибка остановки музыки: {e}")

    # ============================================================
    # ЗАГРУЗКА АССЕТОВ
    # ============================================================
    
    def load_game_assets(self):
        print("🔄 ЗАГРУЗКА АССЕТОВ...")
        
        bg_skin = self.equipped_skins.get("backgrounds", "bg-default")
        print(f"   Фон: {bg_skin}")
        self.background_image = load_asset("backgrounds", bg_skin, GAME_WIDTH, GAME_HEIGHT)
        if self.background_image is None:
            print(f"   ⚠️ Фон не найден, создаю заглушку")
            self.background_image = QPixmap(GAME_WIDTH, GAME_HEIGHT)
            self.background_image.fill(QColor(135, 206, 235))
        else:
            print(f"   ✅ Фон загружен")
        
        bird_skin = self.equipped_skins.get("birds", "bird-default")
        print(f"   Птица: {bird_skin}")
        bird_pixmap = load_asset("birds", bird_skin, bird_width, bird_height)
        if bird_pixmap is None:
            print(f"   ⚠️ Птица не найдена, создаю заглушку")
            bird_pixmap = QPixmap(bird_width, bird_height)
            bird_pixmap.fill(QColor(255, 255, 0))
        else:
            print(f"   ✅ Птица загружена")
        self.bird_image = bird_pixmap
        
        top_pipe_skin = self.equipped_skins.get("pipes_top", "pipe-top-default")
        bottom_pipe_skin = self.equipped_skins.get("pipes_bottom", "pipe-bottom-default")
        
        print(f"   Трубы верх: {top_pipe_skin}")
        print(f"   Трубы низ: {bottom_pipe_skin}")
        
        self.top_pipe_image = load_asset("pipes", top_pipe_skin, pipe_width, pipe_height)
        if self.top_pipe_image is None:
            print(f"   ❌ НЕ НАЙДЕНА: assets/pipes/{top_pipe_skin}.png")
            self.top_pipe_image = QPixmap(pipe_width, pipe_height)
            self.top_pipe_image.fill(QColor(0, 255, 0))
        else:
            print(f"   ✅ Верхняя труба загружена")
        
        self.bottom_pipe_image = load_asset("pipes", bottom_pipe_skin, pipe_width, pipe_height)
        if self.bottom_pipe_image is None:
            print(f"   ❌ НЕ НАЙДЕНА: assets/pipes/{bottom_pipe_skin}.png")
            self.bottom_pipe_image = QPixmap(pipe_width, pipe_height)
            self.bottom_pipe_image.fill(QColor(0, 255, 0))
        else:
            print(f"   ✅ Нижняя труба загружена")
        
        print("✅ ЗАГРУЗКА АССЕТОВ ЗАВЕРШЕНА")

    # ============================================================
    # ЗАГРУЗКА ДАННЫХ ПОЛЬЗОВАТЕЛЯ
    # ============================================================
    
    def load_user_data(self):
        """Загружает данные пользователя из auth_manager"""
        if self.auth_manager.is_authenticated():
            user = self.auth_manager.user
            if user:
                self.best_score = user.get("bestScore", 0)
                self.balance = user.get("balance", 0)
                self.total_score = user.get("totalScore", 0)
                self.games_played = user.get("gamesPlayed", 0)
                print(f"📊 Данные загружены: лучший={self.best_score}, баланс={self.balance}")
        else:
            print("⚠️ Не авторизован, данные не загружены")

    def save_user_stats(self):
        if self.score_saved:
            return
        
        self.score_saved = True
        current_score = int(self.score)
        
        success, message, data = self.api_client.save_game_result(
            current_score,
            self.games_played + 1
        )
        
        if success:
            self.best_score = max(self.best_score, current_score)
            if "newBalance" in data:
                self.balance = data["newBalance"]
            self.total_score += current_score
            self.games_played += 1
            
            if self.auth_manager.is_authenticated():
                self.auth_manager.update_user_data({
                    "bestScore": self.best_score,
                    "balance": self.balance,
                    "totalScore": self.total_score,
                    "gamesPlayed": self.games_played
                })
        else:
            self.save_stats_local(current_score)

    def save_stats_local(self, current_score):
        self.best_score = max(self.best_score, current_score)
        self.balance += current_score
        self.total_score += current_score
        self.games_played += 1
        
        if self.auth_manager.is_authenticated():
            self.auth_manager.update_user_data({
                "bestScore": self.best_score,
                "balance": self.balance,
                "totalScore": self.total_score,
                "gamesPlayed": self.games_played
            })

    # ============================================================
    # ИГРОВАЯ ЛОГИКА
    # ============================================================
    
    def restart_game(self):
        """Перезапускает игру"""
        # ===== ПРОВЕРЯЕМ АВТОРИЗАЦИЮ =====
        if not self.auth_manager.refresh_session():
            print("❌ Не авторизован, скины не обновляются")
            CustomDialog.warning(self, "Ошибка", "❌ Пользователь не авторизован!")
            self.go_to_main_menu()
            return
        
        if self.auth_manager.is_authenticated():
            print("🔄 Обновление скинов при рестарте...")
            self.load_user_data()
            self.skin_manager.sync_with_server()
            self.equipped_skins = self.skin_manager.get_equipped_skins()
            self.load_game_assets()
            self.bird.img = self.bird_image
        else:
            print("⚠️ Не авторизован, скины не обновляются")
        
        self.bird.y = bird_y
        self.pipes.clear()
        self.score = 0
        self.game_over = False
        self.velocity_y = 0
        self.score_saved = False
        self.game_started = True
        self.is_paused = False
        self.go_restart_btn.hide()
        self.go_menu_btn.hide()
        self.pipe_timer.start(self.settings.pipe_interval)
        self.setFocus()
        
        # ===== ЗАПУСКАЕМ МУЗЫКУ =====
        if not self.music_playing and self.settings.sound_enabled:
            self.start_music()

    def create_pipes(self):
        if self.game_over or not self.game_started or self.is_paused:
            return

        random_pipe_y = pipe_y - pipe_height / 4 - random.random() * (pipe_height / 2)
        opening_space = GAME_HEIGHT / 4

        top_pipe = Pipe(self.top_pipe_image)
        top_pipe.y = int(random_pipe_y)
        self.pipes.append(top_pipe)

        bottom_pipe = Pipe(self.bottom_pipe_image)
        bottom_pipe.y = int(top_pipe.y + top_pipe.height + opening_space)
        self.pipes.append(bottom_pipe)

    def move_bird(self):
        if not self.game_started or self.is_paused:
            return
            
        self.velocity_y += self.gravity
        self.bird.y += int(self.velocity_y)

        if self.bird.y < 0:
            self.bird.y = 0

        if self.bird.y > GAME_HEIGHT:
            self.game_over = True
            self.game_started = False
            self.pipe_timer.stop()
            self.save_user_stats()
            self.show_game_over_buttons()
            self.stop_music()
            return

        for pipe in self.pipes:
            pipe.x += self.velocity_x

            if not pipe.passed and self.bird.x > pipe.x + pipe.width:
                self.score += 0.5
                pipe.passed = True

            bird_rect = self.bird.get_rect()
            pipe_rect = pipe.get_rect()
            if bird_rect.intersects(pipe_rect):
                self.game_over = True
                self.game_started = False
                self.pipe_timer.stop()
                self.save_user_stats()
                self.show_game_over_buttons()
                self.stop_music()
                return

        while len(self.pipes) > 0 and self.pipes[0].x < -pipe_width:
            self.pipes.pop(0)

    def show_game_over_buttons(self):
        center_x = GAME_WIDTH // 2
        center_y = GAME_HEIGHT // 2 + 140
        
        self.go_restart_btn.move(center_x - 110, center_y)
        self.go_menu_btn.move(center_x + 10, center_y)
        self.go_restart_btn.show()
        self.go_menu_btn.show()

    # ============================================================
    # ОТРИСОВКА
    # ============================================================
    
    def paintEvent(self, event):
        painter = QPainter(self)

        painter.drawPixmap(0, 0, GAME_WIDTH, GAME_HEIGHT, self.background_image)
        painter.drawPixmap(self.bird.x, self.bird.y, self.bird.width, self.bird.height, self.bird.img)

        for pipe in self.pipes:
            painter.drawPixmap(pipe.x, pipe.y, pipe.width, pipe.height, pipe.img)

        painter.setFont(QFont("Arial", 28, QFont.Bold))
        painter.setPen(QPen(Qt.white))
        painter.drawText(20, 45, f"🪙 {int(self.score)}")

        if self.game_started and not self.game_over and not self.show_main_menu:
            self.draw_user_info(painter)

        if self.is_paused:
            painter.setBrush(Qt.black)
            painter.setOpacity(0.4)
            painter.drawRect(0, 0, GAME_WIDTH, GAME_HEIGHT)
            painter.setOpacity(1.0)
            
            painter.setFont(QFont("Arial", 50, QFont.Bold))
            painter.setPen(QPen(QColor("#0fcf8a")))
            text = "⏸ PAUSED"
            painter.drawText((GAME_WIDTH - painter.fontMetrics().width(text)) // 2, GAME_HEIGHT // 2, text)

        if self.game_over:
            self.draw_game_over_overlay(painter)

        painter.end()

    def draw_user_info(self, painter):
        username_text = f"{self.username}"
        best_text = f"Best: {self.best_score}"
        balance_text = f"💰 {self.balance}"
        
        painter.setFont(QFont("Arial", 20, QFont.Bold))
        username_width = painter.fontMetrics().width(username_text)
        username_height = painter.fontMetrics().height()
        
        painter.setFont(QFont("Arial", 16))
        best_width = painter.fontMetrics().width(best_text)
        balance_width = painter.fontMetrics().width(balance_text)
        text_height = painter.fontMetrics().height()
        
        max_width = max(username_width, best_width, balance_width)
        rect_width = max_width + 30
        rect_height = username_height + text_height + text_height + 30
        rect_x = GAME_WIDTH - rect_width - 15
        rect_y = 10
        
        painter.setBrush(QColor(40, 40, 40, 200))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect_x, rect_y, rect_width, rect_height, 10, 10)
        
        painter.setFont(QFont("Arial", 20, QFont.Bold))
        painter.setPen(QPen(Qt.white))
        painter.drawText(
            rect_x + (rect_width - username_width) // 2,
            rect_y + username_height + 5,
            username_text
        )
        
        painter.setFont(QFont("Arial", 16))
        painter.setPen(QPen(Qt.white))
        painter.drawText(
            rect_x + (rect_width - best_width) // 2,
            rect_y + username_height + text_height + 10,
            best_text
        )
        painter.drawText(
            rect_x + (rect_width - balance_width) // 2,
            rect_y + username_height + text_height * 2 + 15,
            balance_text
        )

    def draw_game_over_overlay(self, painter):
        rect_w, rect_h = 380, 430
        rx = (GAME_WIDTH - rect_w) // 2
        ry = (GAME_HEIGHT - rect_h) // 2
        
        painter.setBrush(QColor(40, 40, 40, 220))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rx, ry, rect_w, rect_h, 20, 20)
        
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.drawRoundedRect(rx, ry, rect_w, rect_h, 20, 20)
        
        cx, cy = rx + rect_w // 2, ry + rect_h // 2
        
        painter.setFont(QFont("Arial", 36, QFont.Bold))
        painter.setPen(QPen(Qt.red))
        text = "GAME OVER"
        painter.drawText(cx - painter.fontMetrics().width(text) // 2, cy - 150, text)

        painter.setFont(QFont("Arial", 24, QFont.Bold))
        painter.setPen(QPen(Qt.white))
        text = f"🪙 {int(self.score)}"
        painter.drawText(cx - painter.fontMetrics().width(text) // 2, cy - 80, text)
        
        painter.setFont(QFont("Arial", 20, QFont.Bold))
        painter.setPen(QPen(QColor("#0fcf8a")))
        text = f"Best: {self.best_score}"
        painter.drawText(cx - painter.fontMetrics().width(text) // 2, cy - 25, text)
        
        text = f"💰 {self.balance}"
        painter.drawText(cx - painter.fontMetrics().width(text) // 2, cy + 20, text)

        painter.setFont(QFont("Arial", 16))
        painter.setPen(QPen(Qt.white))
        text = "SPACE - Restart"
        painter.drawText(cx - painter.fontMetrics().width(text) // 2, cy + 70, text)
        text = "ESC - Menu"
        painter.drawText(cx - painter.fontMetrics().width(text) // 2, cy + 100, text)

    # ============================================================
    # МЕНЮ
    # ============================================================
    
    def init_main_menu(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(50, 80, 50, 80)
        layout.setAlignment(Qt.AlignCenter)

        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0);
                border: 2px solid #0fcf8a;
                border-radius: 16px;
                padding: 20px;
                margin-bottom: 10px;
            }
        """)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(10)
        info_layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Флаппи Логан")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 42px; font-weight: bold; color: #0fcf8a; letter-spacing: 3px;")
        info_layout.addWidget(title)

        user_label = QLabel(f" {self.username}")
        user_label.setAlignment(Qt.AlignCenter)
        user_label.setStyleSheet("font-size: 20px; color: #e0e0e0;")
        info_layout.addWidget(user_label)

        self.stats_label = QLabel(f"Лучший: {self.best_score}  |   💰 Баланс: {self.balance}")
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setStyleSheet("font-size: 20px; color: #e0e0e0;")
        info_layout.addWidget(self.stats_label)

        info_frame.setLayout(info_layout)
        layout.addWidget(info_frame)
        layout.addSpacing(20)

        play_btn = QPushButton("Играть")
        play_btn.setFixedHeight(55)
        play_btn.setFixedWidth(250)
        play_btn.setStyleSheet("""
            QPushButton {
                background-color: #0fcf8a;
                color: white;
                border: none;
                padding: 16px 40px;
                border-radius: 12px;
                font-size: 18px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #0dbd7e; }
        """)
        play_btn.clicked.connect(self.start_game_from_menu)
        layout.addWidget(play_btn, alignment=Qt.AlignCenter)

        settings_btn = QPushButton("Настройки")
        settings_btn.setFixedHeight(55)
        settings_btn.setFixedWidth(250)
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #555555;
                color: white;
                border: none;
                padding: 16px 40px;
                border-radius: 12px;
                font-size: 18px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #666666; }
        """)
        settings_btn.clicked.connect(self.open_settings_from_menu)
        layout.addWidget(settings_btn, alignment=Qt.AlignCenter)

        exit_btn = QPushButton("Выйти из аккаунта")
        exit_btn.setFixedHeight(55)
        exit_btn.setFixedWidth(250)
        exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                color: white;
                border: none;
                padding: 16px 40px;
                border-radius: 12px;
                font-size: 18px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #ff3333; }
        """)
        exit_btn.clicked.connect(self.exit_game)
        layout.addWidget(exit_btn, alignment=Qt.AlignCenter)

        # ===== ГИПЕРССЫЛКА =====
        link_layout = QHBoxLayout()
        link_layout.setAlignment(Qt.AlignCenter)
        
        website_link = Hyperlink("🌐 Наш сайт", Config.WEBSITE_URL)
        link_layout.addWidget(website_link)
        
        layout.addLayout(link_layout)

        self.main_menu_panel.setLayout(layout)

    def init_pause_menu(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(25, 20, 25, 20)

        continue_btn = QPushButton("▶ Продолжить")
        continue_btn.setFixedHeight(50)
        continue_btn.setStyleSheet("""
            QPushButton {
                background-color: #0fcf8a;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 18px;
                font-weight: 700;
            }
            QPushButton:hover { background-color: #0dbd7e; }
        """)
        continue_btn.clicked.connect(self.close_pause_menu)
        layout.addWidget(continue_btn)

        settings_frame = QFrame()
        settings_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 30, 30, 180);
                border-radius: 12px;
                padding: 15px;
            }
        """)
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(10)

        diff_layout = QHBoxLayout()
        diff_layout.setSpacing(10)
        diff_label = QLabel("Сложность:")
        diff_label.setStyleSheet("font-size: 16px; font-weight: 700; color: #e0e0e0;")
        diff_layout.addWidget(diff_label)
        
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["Легкая", "Нормальная", "Сложная"])
        self.difficulty_combo.setCurrentText(self.get_difficulty_text())
        self.difficulty_combo.currentTextChanged.connect(self.change_difficulty)
        diff_layout.addWidget(self.difficulty_combo)
        diff_layout.addStretch()
        settings_layout.addLayout(diff_layout)

        sound_layout = QHBoxLayout()
        sound_layout.setSpacing(10)
        sound_label = QLabel("Звук:")
        sound_label.setStyleSheet("font-size: 16px; font-weight: 700; color: #e0e0e0;")
        sound_layout.addWidget(sound_label)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(80)
        self.volume_slider.valueChanged.connect(self.change_volume)
        sound_layout.addWidget(self.volume_slider)
        
        self.volume_value = QLabel(f"{self.volume_slider.value()}%")
        self.volume_value.setObjectName("value_label")
        sound_layout.addWidget(self.volume_value)
        
        self.mute_btn = QPushButton("🔇" if self.volume_slider.value() == 0 else "🔊")
        self.mute_btn.setFixedHeight(35)
        self.mute_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888888;
                border: 2px solid #333333;
                border-radius: 8px;
                padding: 4px 10px;
                font-size: 18px;
                font-weight: 600;
                min-width: 35px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.05);
                border-color: #0fcf8a;
            }
        """)
        self.mute_btn.clicked.connect(self.toggle_mute)
        sound_layout.addWidget(self.mute_btn)
        
        settings_layout.addLayout(sound_layout)
        settings_frame.setLayout(settings_layout)
        layout.addWidget(settings_frame)

        for text, slot, style in [
            ("Сохранить настройки", self.save_settings, "background-color: #0fcf8a;"),
            ("Главное меню", self.go_to_main_menu, "background-color: transparent; color: #e0e0e0; border: 2px solid #555555;"),
            ("Выйти из аккаунта", self.exit_game, "background-color: transparent; color: #ff4444; border: 2px solid #ff4444;"),
        ]:
            btn = QPushButton(text)
            btn.setFixedHeight(45)
            btn.setStyleSheet(f"""
                QPushButton {{
                    {style}
                    border-radius: 10px;
                    font-size: 17px;
                    font-weight: 700;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 255, 255, 0.05);
                }}
            """)
            btn.clicked.connect(slot)
            layout.addWidget(btn)

        # ===== ГИПЕРССЫЛКА =====
        link_layout = QHBoxLayout()
        link_layout.setAlignment(Qt.AlignCenter)
        
        website_link = Hyperlink("🌐 Наш сайт", Config.WEBSITE_URL)
        link_layout.addWidget(website_link)
        
        layout.addLayout(link_layout)

        self.menu_panel.setLayout(layout)

    # ============================================================
    # НАСТРОЙКИ
    # ============================================================
    
    def get_difficulty_text(self):
        return {"easy": "Легкая", "normal": "Нормальная", "hard": "Сложная"}.get(
            self.settings.difficulty, "Нормальная"
        )

    def change_difficulty(self, text):
        diff_map = {"Легкая": "easy", "Нормальная": "normal", "Сложная": "hard"}
        self.settings.difficulty = diff_map.get(text, "normal")
        
        params = {
            "easy": {"gravity": 0.4, "jump_power": -10, "pipe_speed": -2, "pipe_interval": 1800},
            "normal": {"gravity": 0.6, "jump_power": -9, "pipe_speed": -3, "pipe_interval": 1500},
            "hard": {"gravity": 0.8, "jump_power": -7, "pipe_speed": -5, "pipe_interval": 1200}
        }[self.settings.difficulty]
        
        self.settings.gravity = params["gravity"]
        self.settings.jump_power = params["jump_power"]
        self.settings.pipe_speed = params["pipe_speed"]
        self.settings.pipe_interval = params["pipe_interval"]
        
        self.gravity = self.settings.gravity
        self.velocity_x = self.settings.pipe_speed
        
        if self.game_started and not self.game_over and not self.is_paused:
            self.pipe_timer.stop()
            self.pipe_timer.start(self.settings.pipe_interval)

    def change_volume(self):
        volume = self.volume_slider.value()
        self.volume_value.setText(f"{volume}%")
        self.player.setVolume(volume)
        self.settings.volume = volume
        self.settings.sound_enabled = volume > 0
        self.mute_btn.setText("🔇" if volume == 0 else "🔊")
        
        # ===== ТОЛЬКО ОСТАНАВЛИВАЕМ МУЗЫКУ, ЕСЛИ ЗВУК ВЫКЛЮЧЕН =====
        # НЕ ЗАПУСКАЕМ МУЗЫКУ ПРИ ИЗМЕНЕНИИ ГРОМКОСТИ!
        if volume == 0 and self.music_playing:
            self.stop_music()

    def toggle_mute(self):
        if self.volume_slider.value() > 0:
            self.volume_slider.setValue(0)
            self.mute_btn.setText("🔇")
            self.settings.sound_enabled = False
            self.settings.volume = 0
            self.player.setVolume(0)
            if self.music_playing:
                self.stop_music()
        else:
            self.volume_slider.setValue(80)
            self.mute_btn.setText("🔊")
            self.settings.sound_enabled = True
            self.settings.volume = 80
            self.player.setVolume(80)
            # ===== НЕ ЗАПУСКАЕМ МУЗЫКУ АВТОМАТИЧЕСКИ =====
        self.volume_value.setText(f"{self.volume_slider.value()}%")

    def save_settings(self):
        self.settings.save_settings()
        CustomDialog.information(self, "Успех", "✅ Настройки сохранены!")

    # ============================================================
    # УПРАВЛЕНИЕ МЕНЮ
    # ============================================================
    
    def start_game_from_menu(self):
        """Запускает игру из главного меню"""
        # ===== ПРОВЕРЯЕМ АВТОРИЗАЦИЮ =====
        if not self.auth_manager.refresh_session():
            print("❌ Не авторизован, скины не обновляются")
            CustomDialog.warning(self, "Ошибка", "❌ Пользователь не авторизован!\nПожалуйста, войдите заново.")
            self.go_to_main_menu()
            return
        
        if self.auth_manager.is_authenticated():
            print(f"✅ Пользователь авторизован: {self.auth_manager.get_username()}")
            print("🔄 Обновление скинов перед игрой...")
            
            # Обновляем данные пользователя
            self.load_user_data()
            
            # Синхронизируем скины
            self.skin_manager.sync_with_server()
            self.equipped_skins = self.skin_manager.get_equipped_skins()
            
            # Загружаем ассеты
            self.load_game_assets()
            self.bird.img = self.bird_image
            
            # Обновляем статистику в меню
            self.update_main_menu_stats()
        else:
            print("❌ Не авторизован, скины не обновляются")
            CustomDialog.warning(self, "Ошибка", "❌ Пользователь не авторизован!\nПожалуйста, войдите заново.")
            self.go_to_main_menu()
            return
        
        self.main_menu_panel.hide()
        self.overlay.hide()
        self.show_main_menu = False
        self.game_started = True
        self.is_paused = False
        self.is_settings_from_menu = False
        self.go_restart_btn.hide()
        self.go_menu_btn.hide()
        self.pipe_timer.start(self.settings.pipe_interval)
        self.setFocus()
        
        # ===== ЗАПУСКАЕМ МУЗЫКУ =====
        if self.settings.sound_enabled and not self.music_playing:
            self.start_music()

    def open_settings_from_menu(self):
        self.is_settings_from_menu = True
        self.overlay.show()
        self.menu_panel.show()
        self.menu_visible = True
        self.difficulty_combo.setCurrentText(self.get_difficulty_text())
        volume = self.settings.volume if hasattr(self.settings, 'volume') else 80
        self.volume_slider.setValue(volume)
        self.volume_value.setText(f"{volume}%")
        self.mute_btn.setText("🔇" if volume == 0 else "🔊")

    def close_pause_menu(self):
        self.menu_panel.hide()
        self.menu_visible = False
        
        if self.is_settings_from_menu:
            self.is_settings_from_menu = False
            self.overlay.hide()
            self.show_main_menu = True
            self.main_menu_panel.show()
            self.update_main_menu_stats()
            self.go_restart_btn.hide()
            self.go_menu_btn.hide()
            return
        
        if self.is_paused:
            self.is_paused = False
            if self.game_started and not self.game_over:
                self.pipe_timer.start(self.settings.pipe_interval)
                # ===== ЗАПУСКАЕМ МУЗЫКУ ПРИ ПРОДОЛЖЕНИИ =====
                if self.settings.sound_enabled and not self.music_playing:
                    self.start_music()
        
        self.setFocus()

    def go_to_main_menu(self):
        # ===== ОСТАНАВЛИВАЕМ МУЗЫКУ ПРИ ВЫХОДЕ В МЕНЮ =====
        if self.music_playing:
            self.stop_music()
        
        if self.is_settings_from_menu:
            self.menu_panel.hide()
            self.menu_visible = False
            self.is_settings_from_menu = False
            self.overlay.hide()
            self.show_main_menu = True
            self.main_menu_panel.show()
            self.update_main_menu_stats()
            self.go_restart_btn.hide()
            self.go_menu_btn.hide()
            return
        
        if self.game_over:
            self.game_started = False
            self.game_over = False
            self.pipe_timer.stop()
            self.pipes.clear()
            self.score = 0
            self.bird.y = bird_y
            self.velocity_y = 0
            self.menu_panel.hide()
            self.menu_visible = False
            self.is_paused = False
            self.is_settings_from_menu = False
            self.overlay.hide()
            self.show_main_menu = True
            self.main_menu_panel.show()
            self.update_main_menu_stats()
            self.go_restart_btn.hide()
            self.go_menu_btn.hide()
            return
        
        if CustomDialog.question(self, 'В главное меню', 'Вы уверены, что хотите выйти в главное меню?\nПрогресс игры будет потерян.') == QMessageBox.Yes:
            self.game_started = False
            self.game_over = False
            self.pipe_timer.stop()
            self.pipes.clear()
            self.score = 0
            self.bird.y = bird_y
            self.velocity_y = 0
            self.menu_panel.hide()
            self.menu_visible = False
            self.is_paused = False
            self.is_settings_from_menu = False
            self.overlay.hide()
            self.show_main_menu = True
            self.main_menu_panel.show()
            self.update_main_menu_stats()
            self.go_restart_btn.hide()
            self.go_menu_btn.hide()

    def update_main_menu_stats(self):
        """Обновляет статистику в главном меню"""
        # ===== ПРОВЕРЯЕМ АВТОРИЗАЦИЮ =====
        if not self.auth_manager.refresh_session():
            print("⚠️ Не авторизован, статистика не обновляется")
            self.stats_label.setText(f"Лучший: {self.best_score}  |   💰 Баланс: {self.balance}")
            return
        
        if self.auth_manager.is_authenticated():
            print("🔄 Обновление скинов с сервера...")
            self.skin_manager.sync_with_server()
            self.equipped_skins = self.skin_manager.get_equipped_skins()
            self.load_game_assets()
            self.bird.img = self.bird_image
            
            # Получаем лучший счет с сервера
            success, _, best_score = self.api_client.get_best_score()
            if success:
                self.auth_manager.update_user_data({"bestScore": best_score})
            
            # Обновляем данные
            self.load_user_data()
        
        self.stats_label.setText(f"Лучший: {self.best_score}  |   💰 Баланс: {self.balance}")

    # ============================================================
    # ВЫХОД ИЗ АККАУНТА
    # ============================================================
    
    def exit_game(self):
        """Выход из аккаунта"""
        if self.music_playing:
            self.stop_music()
        
        if CustomDialog.question(self, 'Выход из аккаунта', 'Вы уверены, что хотите выйти из аккаунта?') == QMessageBox.Yes:
            self.game_timer.stop()
            self.pipe_timer.stop()
            self.auth_manager.clear_session()
            self.close()
            from registration import RegistrationWindow
            self.registration_window = RegistrationWindow()
            self.registration_window.show()

    # ============================================================
    # ОБРАБОТКА СОБЫТИЙ
    # ============================================================
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self.show_main_menu:
                return
            if self.game_over:
                self.go_to_main_menu()
                return
            if self.menu_visible:
                self.close_pause_menu()
                return
            
            if not self.game_started:
                self.open_settings_from_menu()
                return
            
            # Открываем меню паузы
            self.menu_panel.show()
            self.menu_visible = True
            if self.game_started and not self.game_over:
                self.is_paused = True
                self.pipe_timer.stop()
                # ===== ОСТАНАВЛИВАЕМ МУЗЫКУ ПРИ ПАУЗЕ =====
                if self.music_playing:
                    self.stop_music()
            self.difficulty_combo.setCurrentText(self.get_difficulty_text())
            volume = self.settings.volume if hasattr(self.settings, 'volume') else 80
            self.volume_slider.setValue(volume)
            self.volume_value.setText(f"{volume}%")
            self.mute_btn.setText("🔇" if volume == 0 else "🔊")
            return
            
        if event.key() in (Qt.Key_Space, Qt.Key_X, Qt.Key_Up):
            if self.show_main_menu:
                return
            if self.game_over:
                self.restart_game()
            elif not self.game_started:
                self.game_started = True
                self.is_paused = False
                self.pipe_timer.start(self.settings.pipe_interval)
                # ===== ЗАПУСКАЕМ МУЗЫКУ =====
                if self.settings.sound_enabled and not self.music_playing:
                    self.start_music()
            elif not self.is_paused:
                self.velocity_y = self.settings.jump_power

    def game_loop(self):
        self.move_bird()
        self.update()

    def closeEvent(self, event):
        self.stop_music()
        self.game_timer.stop()
        self.pipe_timer.stop()
        event.accept()