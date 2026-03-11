from PySide6.QtWidgets import QWidget, QVBoxLayout
from src.core.config import ConfigManager
from src.core.session_manager import SessionManager
from src.frontend.widgets.main_widget import (
    MainWidget,
)  # Verify if import matches your project


class MainTab(QWidget):
    """
    Main tab wrapper for the receiving module.
    Handles the injection of dependencies and connection status into the main widget.
    """

    def __init__(
        self,
        config_manager: ConfigManager,
        session_manager: SessionManager,
        is_connected: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self.config_manager = config_manager
        self.session_manager = session_manager
        self.is_connected = is_connected

        self.setup_ui()

    def setup_ui(self) -> None:
        """Sets up the layout and loads the main functional widget."""
        main_layout = QVBoxLayout(self)

        self.main_widget = MainWidget(
            self.config_manager, self.session_manager, self.is_connected
        )

        main_layout.addWidget(self.main_widget)
        self.setLayout(main_layout)
