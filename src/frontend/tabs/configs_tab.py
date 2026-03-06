from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from src.frontend.widgets.configs_widget import ConfigsWidget
from src.core.config import ConfigManager
from src.utils.printer import PrinterManager

class ConfigsTab(QWidget):
    def __init__(self, config_manager: ConfigManager, printer_manager: PrinterManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.printer_manager = printer_manager
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        title_label = QLabel("Configurações")
        layout.addWidget(title_label)
        layout.addWidget(ConfigsWidget(self.config_manager, self.printer_manager))