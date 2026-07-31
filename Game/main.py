import sys
import os
from PyQt5.QtWidgets import QApplication

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.registration import LoginWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Всегда открываем окно входа
    window = LoginWindow(registration_window=None)
    window.show()
    
    sys.exit(app.exec_())
