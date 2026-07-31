
from PyQt5.QtWidgets import QDialog, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt5.QtCore import Qt


class CustomDialog(QDialog):

    
    def __init__(self, parent, title, message, is_warning=False, buttons=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(450, 200)
        self.setModal(True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        if buttons is None:
            buttons = [("OK", "ok")]
        
        self.container = QFrame(self)
        self.container.setGeometry(0, 0, 450, 200)
        
        border_color = "#ff4444" if is_warning else "#0fcf8a"
            
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: #0a0a0a;
                border: 2px solid {border_color};
                border-radius: 16px;
            }}
            QLabel {{
                color: #e0e0e0;
                font-size: 16px;
            }}
            QPushButton {{
                background-color: #0fcf8a;
                color: white;
                border: none;
                padding: 10px 30px;
                border-radius: 8px;
                font-size: 15px;
                font-weight: 600;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: #0dbd7e;
            }}
            QPushButton:pressed {{
                background-color: #0caa70;
            }}
            QPushButton#yes_btn {{
                background-color: #ff4444;
            }}
            QPushButton#yes_btn:hover {{
                background-color: #ff3333;
            }}
            QPushButton#no_btn {{
                background-color: #333333;
                color: #e0e0e0;
            }}
            QPushButton#no_btn:hover {{
                background-color: #444444;
            }}
            QPushButton#ok_btn {{
                background-color: #0fcf8a;
            }}
            QPushButton#ok_btn:hover {{
                background-color: #0dbd7e;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {border_color};")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        msg_label = QLabel(message)
        msg_label.setAlignment(Qt.AlignCenter)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        btn_layout.setAlignment(Qt.AlignCenter)
        
        for text, action in buttons:
            btn = QPushButton(text)
            if action == "yes":
                btn.setObjectName("yes_btn")
                btn.clicked.connect(self.accept)
            elif action == "no":
                btn.setObjectName("no_btn")
                btn.clicked.connect(self.reject)
            else:
                btn.setObjectName("ok_btn")
                btn.clicked.connect(self.accept)
            btn.setFixedHeight(40)
            btn_layout.addWidget(btn)
        
        layout.addLayout(btn_layout)
        self.container.setLayout(layout)
        self.drag_pos = None
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_pos is not None:
            self.move(event.globalPos() - self.drag_pos)
    
    def mouseReleaseEvent(self, event):
        self.drag_pos = None
    
    @staticmethod
    def question(parent, title, message):
        dialog = CustomDialog(
            parent, title, message,
            is_warning=False,
            buttons=[("Нет", "no"), ("Да", "yes")]
        )
        return QMessageBox.Yes if dialog.exec_() == QDialog.Accepted else QMessageBox.No
    
    @staticmethod
    def information(parent, title, message):
        dialog = CustomDialog(parent, title, message, is_warning=False, buttons=[("OK", "ok")])
        dialog.exec_()
    
    @staticmethod
    def warning(parent, title, message):
        dialog = CustomDialog(parent, title, message, is_warning=True, buttons=[("OK", "ok")])
        dialog.exec_()
