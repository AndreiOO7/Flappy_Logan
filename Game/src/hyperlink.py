
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices


class Hyperlink(QLabel):
    """Кликбельная гиперссылка"""
    
    def __init__(self, text, url, parent=None):
        super().__init__(text, parent)
        self.url = url
        self.setStyleSheet("""
            QLabel {
                color: #0fcf8a;
                font-size: 14px;
                font-weight: 500;
                text-decoration: underline;
            }
            QLabel:hover {
                color: #0dbd7e;
            }
        """)
        self.setCursor(Qt.PointingHandCursor)
        self.setAlignment(Qt.AlignCenter)
    
    def mousePressEvent(self, event):
        """Открывает ссылку в браузере при клике"""
        QDesktopServices.openUrl(QUrl(self.url))
