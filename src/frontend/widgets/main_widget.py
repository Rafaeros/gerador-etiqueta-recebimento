from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
)
from src.core.config import ConfigManager
from src.core.session_manager import SessionManager
from src.frontend.widgets.search_nfe_data_widget import SearchNfeDataWidget


class MainWidget(QWidget):
    """Main widget handling the purchase ID input and search logic."""

    def __init__(
        self,
        config_manager: ConfigManager,
        session_manager: SessionManager,
        parent=None,
    ):
        super().__init__(parent)
        self.config_manager = config_manager
        self.session_manager = session_manager
        self.setup_ui()

    def setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(SearchNfeDataWidget(self.session_manager, self.config_manager))
        self.setLayout(main_layout)
