import re
from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton, 
                             QVBoxLayout, QFrame, QHBoxLayout)
from PyQt5.QtCore import Qt

from utils import center_window
from dialogs import CustomDialog
from game import FlappyBird
from auth_manager import AuthManager
from network import APIClient
from config import Config
from hyperlink import Hyperlink

class RegistrationWindow(QWidget):
    """Окно регистрации нового пользователя"""
    
    def __init__(self):
        super().__init__()
        self.auth_manager = AuthManager()
        self.api_client = APIClient(self.auth_manager)
        
        self._pending_password = ""
        self._pending_username = ""
        
        self.setWindowTitle("Флаппи Логан - Регистрация")
        self.setFixedSize(500, 750)
        self.setStyleSheet("""
            QWidget {
                background-color: #000000;
            }
            QLabel {
                color: #e0e0e0;
                font-size: 15px;
                font-weight: 500;
            }
            QLineEdit {
                padding: 14px 16px;
                border: 1px solid #2a2a2a;
                border-radius: 8px;
                font-size: 15px;
                background-color: #141414;
                color: #e0e0e0;
            }
            QLineEdit:focus {
                border: 1px solid #0fcf8a;
            }
            QLineEdit::placeholder {
                color: #666666;
            }
            QPushButton {
                background-color: #0fcf8a;
                color: white;
                border: none;
                padding: 16px;
                border-radius: 8px;
                font-size: 17px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #0dbd7e;
            }
            QPushButton#login_btn {
                background-color: transparent;
                color: #888888;
                border: none;
                font-size: 15px;
                padding: 14px;
            }
            QPushButton#login_btn:hover {
                color: #0fcf8a;
            }
        """)

        center_window(self)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(18)
        main_layout.setContentsMargins(60, 50, 60, 50)

        title = QLabel("Флаппи Логан")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 40px; font-weight: bold; color: #0fcf8a; letter-spacing: 3px;")
        main_layout.addWidget(title)

        subtitle = QLabel("Создайте аккаунт и начните играть")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 16px; color: #888888; margin-bottom: 10px;")
        main_layout.addWidget(subtitle)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #2a2a2a; margin: 5px 0;")
        main_layout.addWidget(line)

        username_label = QLabel("Имя пользователя")
        username_label.setStyleSheet("color: #e0e0e0; font-size: 15px; font-weight: 500;")
        main_layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("3-20 символов (A-Z, a-z, 0-9)")
        self.username_input.setMinimumHeight(48)
        self.username_input.returnPressed.connect(self.register)
        main_layout.addWidget(self.username_input)

        password_label = QLabel("Пароль")
        password_label.setStyleSheet("color: #e0e0e0; font-size: 15px; font-weight: 500;")
        main_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введите пароль (минимум 4 символа)")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(48)
        self.password_input.returnPressed.connect(self.register)
        main_layout.addWidget(self.password_input)

        confirm_label = QLabel("Подтвердите пароль")
        confirm_label.setStyleSheet("color: #e0e0e0; font-size: 15px; font-weight: 500;")
        main_layout.addWidget(confirm_label)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Повторите пароль")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setMinimumHeight(48)
        self.confirm_password_input.returnPressed.connect(self.register)
        main_layout.addWidget(self.confirm_password_input)

        self.register_button = QPushButton("Зарегистрироваться")
        self.register_button.setMinimumHeight(55)
        self.register_button.clicked.connect(self.register)
        main_layout.addWidget(self.register_button)

        info_label = QLabel("Пароль должен содержать минимум 4 символа")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("font-size: 12px; color: #666666;")
        main_layout.addWidget(info_label)

        self.login_button = QPushButton("Уже есть аккаунт? Войти")
        self.login_button.setObjectName("login_btn")
        self.login_button.setMinimumHeight(50)
        self.login_button.clicked.connect(self.show_login)
        main_layout.addWidget(self.login_button)

        link_layout = QHBoxLayout()
        link_layout.setAlignment(Qt.AlignCenter)
        website_link = Hyperlink("Наш сайт", Config.WEBSITE_URL)
        link_layout.addWidget(website_link)
        main_layout.addLayout(link_layout)

        main_layout.addStretch()
        self.setLayout(main_layout)


    def register(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not username:
            CustomDialog.warning(self, "Ошибка", "Введите имя пользователя!")
            return

        if len(username) < 3:
            CustomDialog.warning(self, "Ошибка", "Имя пользователя должно содержать минимум 3 символа!")
            return

        if len(username) > 20:
            CustomDialog.warning(self, "Ошибка", "Имя пользователя должно содержать максимум 20 символов!")
            return

        if not re.match(r'^[a-zA-Z0-9]+$', username):
            CustomDialog.warning(self, "Ошибка", 
                "Имя пользователя может содержать только:\n"
                "- английские буквы (A-Z, a-z)\n"
                "- цифры (0-9)")
            return

        if not password:
            CustomDialog.warning(self, "Ошибка", "Введите пароль!")
            return

        if len(password) < 4:
            CustomDialog.warning(self, "Ошибка", "Пароль должен содержать минимум 4 символа!")
            return

        if password != confirm_password:
            CustomDialog.warning(self, "Ошибка", "Пароли не совпадают!")
            return

        self._pending_username = username
        self._pending_password = password

        self.register_button.setEnabled(False)
        self.register_button.setText("Отправка...")

        # Асинхронная регистрация
        self.api_client.register_async(username, password, self._on_register_complete)

    def _on_register_complete(self, success, message, user_data):
        """Обработчик завершения регистрации"""
        self.register_button.setEnabled(True)
        self.register_button.setText("Зарегистрироваться")
        
        if not success:
            CustomDialog.warning(self, "Ошибка", f"{message}")
            return
        
        CustomDialog.information(self, "Успех", f"{message}")
        
        username = self._pending_username
        password = self._pending_password
        
        if username and password:
            print(f"Автоматический вход для: {username}")
            
            # Синхронный вход
            login_success, login_message, login_data = self.api_client.login(username, password)
            
            if login_success:
                print(f"Вход выполнен для: {username}")
                self.open_game(username)
            else:
                print(f"Вход не удался: {login_message}")
                self.show_login()
        else:
            self.show_login()

    def show_login(self):
        self.login_window = LoginWindow(self)
        self.login_window.show()
        self.hide()

    def open_game(self, username):
        """Открывает игру для пользователя"""
        print(f"Открываю игру для: {username}")
        
        if not username:
            CustomDialog.warning(self, "Ошибка", "Не удалось определить пользователя!")
            return
        
        if not self.auth_manager.is_authenticated():
            CustomDialog.warning(self, "Ошибка", "Вы не авторизованы!")
            return
        
        self.game_window = FlappyBird(username, self, self.auth_manager)
        self.game_window.show()
        self.hide()


class LoginWindow(QWidget):
    """Окно входа пользователя"""
    
    def __init__(self, registration_window=None):
        super().__init__()
        self.registration_window = registration_window
        
        self.auth_manager = AuthManager()
        self.api_client = APIClient(self.auth_manager)
        
        self.setWindowTitle("Флаппи Логан - Вход")
        self.setFixedSize(500, 700)
        self.setStyleSheet("""
            QWidget {
                background-color: #000000;
            }
            QLabel {
                color: #e0e0e0;
                font-size: 15px;
                font-weight: 500;
            }
            QLineEdit {
                padding: 14px 16px;
                border: 1px solid #2a2a2a;
                border-radius: 8px;
                font-size: 15px;
                background-color: #141414;
                color: #e0e0e0;
            }
            QLineEdit:focus {
                border: 1px solid #0fcf8a;
            }
            QLineEdit::placeholder {
                color: #666666;
            }
            QPushButton {
                background-color: #0fcf8a;
                color: white;
                border: none;
                padding: 16px;
                border-radius: 8px;
                font-size: 17px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #0dbd7e;
            }
            QPushButton#back_btn {
                background-color: transparent;
                color: #888888;
                border: none;
                font-size: 15px;
                padding: 14px;
            }
            QPushButton#back_btn:hover {
                color: #0fcf8a;
            }
        """)

        center_window(self)

        layout = QVBoxLayout()
        layout.setSpacing(18)
        layout.setContentsMargins(60, 50, 60, 50)

        title = QLabel("Флаппи Логан")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 40px; font-weight: bold; color: #0fcf8a; letter-spacing: 3px;")
        layout.addWidget(title)

        subtitle = QLabel("Войдите в аккаунт")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 16px; color: #888888; margin-bottom: 10px;")
        layout.addWidget(subtitle)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #2a2a2a; margin: 5px 0;")
        layout.addWidget(line)

        layout.addWidget(QLabel("Имя пользователя"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Введите имя пользователя")
        self.username_input.setMinimumHeight(48)
        self.username_input.returnPressed.connect(self.login)
        layout.addWidget(self.username_input)

        layout.addWidget(QLabel("Пароль"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(48)
        self.password_input.returnPressed.connect(self.login)
        layout.addWidget(self.password_input)

        self.login_button = QPushButton("Войти")
        self.login_button.setMinimumHeight(55)
        self.login_button.clicked.connect(self.login)
        layout.addWidget(self.login_button)

        self.back_button = QPushButton("Назад к регистрации")
        self.back_button.setObjectName("back_btn")
        self.back_button.setMinimumHeight(50)
        self.back_button.clicked.connect(self.go_back)
        layout.addWidget(self.back_button)

        link_layout = QHBoxLayout()
        link_layout.setAlignment(Qt.AlignCenter)
        website_link = Hyperlink("Наш сайт", Config.WEBSITE_URL)
        link_layout.addWidget(website_link)
        layout.addLayout(link_layout)

        layout.addStretch()
        self.setLayout(layout)

    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username:
            CustomDialog.warning(self, "Ошибка", "Введите имя пользователя!")
            return

        if not password:
            CustomDialog.warning(self, "Ошибка", "Введите пароль!")
            return

        self.login_button.setEnabled(False)
        self.login_button.setText("Вход...")

        # Синхронный вход
        success, message, user_data = self.api_client.login(username, password)

        self.login_button.setEnabled(True)
        self.login_button.setText("Войти")

        if success:
            print(f"Вход выполнен для: {username}")
            CustomDialog.information(self, "Успех", f"{message}")
            if self.registration_window:
                self.registration_window.open_game(username)
            else:
                from game import FlappyBird
                self.game_window = FlappyBird(username, None, self.auth_manager)
                self.game_window.show()
            self.close()
        else:
            CustomDialog.warning(self, "Ошибка", f"{message}")

    def go_back(self):
        """Возвращает пользователя к окну регистрации"""
        if self.registration_window:
            self.registration_window.show()
        else:
            from registration import RegistrationWindow
            self.registration_window = RegistrationWindow()
            self.registration_window.show()
        self.close()
