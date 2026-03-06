from PySide6.QtWidgets import QWidget, QVBoxLayout
from src.frontend.widgets.main_widget import MainWidget


class MainTab(QWidget):
    def __init__(self, config_manager, session_manager):
        super().__init__()
        self.config_manager = config_manager
        self.session_manager = session_manager
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(
            MainWidget(self.config_manager, self.session_manager)
        )
        self.setLayout(self.main_layout)
