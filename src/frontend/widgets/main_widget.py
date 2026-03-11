from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtCore import Qt
from src.core.config import ConfigManager
from src.core.session_manager import SessionManager
from src.frontend.widgets.search_nfe_data_widget import SearchNfeDataWidget


class MainWidget(QWidget):
    """
    Main widget handling the purchase ID input and search logic.
    Includes a fallback UI for offline mode if the connection fails.
    """

    def __init__(
        self,
        config_manager: ConfigManager,
        session_manager: SessionManager,
        is_connected: bool = True,  # <-- ADD THIS ARGUMENT
        parent=None,
    ):
        super().__init__(parent)
        self.config_manager = config_manager
        self.session_manager = session_manager
        self.is_connected = is_connected

        self.setup_ui()

    def setup_ui(self) -> None:
        """Renders either the search widget or the offline fallback based on connection status."""
        main_layout = QVBoxLayout(self)

        if self.is_connected:
            # --- ONLINE MODE: Render standard search widget ---
            main_layout.addWidget(
                SearchNfeDataWidget(self.session_manager, self.config_manager)
            )
        else:
            # --- OFFLINE MODE: Render stylized fallback UI ---
            fallback_layout = QVBoxLayout()
            fallback_layout.addStretch()

            lbl_icon = QLabel("⚠️")
            lbl_icon.setAlignment(Qt.AlignCenter)
            lbl_icon.setStyleSheet(
                "font-size: 72px; margin-bottom: 10px; background: transparent; border: none;"
            )
            fallback_layout.addWidget(lbl_icon)

            lbl_title = QLabel("Modo Offline (Desconectado)")
            lbl_title.setAlignment(Qt.AlignCenter)
            lbl_title.setStyleSheet(
                "font-size: 24px; font-weight: bold; color: #0f172a; background: transparent; border: none;"
            )
            fallback_layout.addWidget(lbl_title)

            lbl_desc = QLabel(
                "Não foi possível conectar ao sistema CargaMáquina.\n"
                "Verifique sua conexão com a internet ou se as credenciais em 'Configurações' estão corretas."
            )
            lbl_desc.setAlignment(Qt.AlignCenter)
            lbl_desc.setStyleSheet(
                "font-size: 16px; color: #475569; margin-top: 10px; background: transparent; border: none;"
            )
            fallback_layout.addWidget(lbl_desc)

            lbl_tip = QLabel(
                "💡 Dica: Você ainda pode usar a aba 'Manual' para gerar etiquetas locais."
            )
            lbl_tip.setAlignment(Qt.AlignCenter)
            lbl_tip.setStyleSheet(
                "font-size: 14px; font-weight: bold; color: #7609e8; margin-top: 20px; background: transparent; border: none;"
            )
            fallback_layout.addWidget(lbl_tip)

            fallback_layout.addStretch()
            main_layout.addLayout(fallback_layout)

        self.setLayout(main_layout)
