from PySide6.QtWidgets import QWidget, QVBoxLayout
from src.core.config import ConfigManager
from src.frontend.widgets.session_config_widget import SessionConfigWidget
from src.utils.printer import PrinterManager
from src.frontend.widgets.printer_selection_widget import PrinterSelectionWidget


class ConfigsWidget(QWidget):
    def __init__(
        self,
        config_manager: ConfigManager,
        printer_manager: PrinterManager,
        parent=None,
    ):
        super().__init__(parent)
        self.config_manager = config_manager
        self.printer_manager = printer_manager
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(SessionConfigWidget(self.config_manager))
        layout.addWidget(
            PrinterSelectionWidget(self.config_manager, self.printer_manager)
        )
        layout.addStretch()
