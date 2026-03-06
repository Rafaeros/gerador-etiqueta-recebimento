import asyncio
from PySide6.QtWidgets import QMainWindow, QTabWidget
from PySide6.QtGui import QCloseEvent
from src.core.config import ConfigManager
from src.core.session_manager import SessionManager
from src.frontend.tabs.main_tab import MainTab
from src.frontend.tabs.configs_tab import ConfigsTab
from src.utils.printer import PrinterManager


class Interface(QMainWindow):
    """Main window of the system, responsible for managing widgets and tabs."""

    def __init__(
        self,
        config_manager: ConfigManager,
        printer_manager: PrinterManager,
        session_manager: SessionManager,
    ):
        super().__init__()
        self.config_manager = config_manager
        self.printer_manager = printer_manager
        self.session_manager = session_manager

        self.setWindowTitle("Gerador de Etiqueta de Recebimento")

        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface layout and components."""
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.tabs.currentChanged.connect(self.tab_changed)

        self.tabs.addTab(
            MainTab(self.config_manager, self.session_manager), "Recebimento"
        )
        self.tabs.addTab(
            ConfigsTab(self.config_manager, self.printer_manager), "Configurações"
        )
        self.tabs.setCurrentIndex(0)

        self.show()

    def tab_changed(self, index):
        """Handle tab change event, allowing for any necessary updates when switching tabs."""
        print("tab changed to ", index)

    def closeEvent(self, event: QCloseEvent):
        """Handle application close event, ensuring proper cleanup of resources."""
        if self.session_manager and hasattr(self.session_manager, "session"):
            asyncio.create_task(self.session_manager.session.close())
        event.accept()
