from PySide6.QtWidgets import (
    QWidget,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
)
from src.core.config import ConfigManager


class SessionConfigWidget(QWidget):
    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Digite seu usuário")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Digite sua senha")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.btn_save = QPushButton("Salvar")
        self.btn_save.setObjectName("primary")
        self.btn_save.clicked.connect(self.save_config)

        form_layout.addRow("Usuário:", self.username_input)
        form_layout.addRow("Senha:", self.password_input)

        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.btn_save)
        main_layout.addStretch()

    def load_config(self):
        """Load existing session configuration from the ConfigManager."""
        session_config = self.config_manager.get_session_config()
        if session_config:
            self.username_input.setText(session_config.get("username", ""))
            self.password_input.setText(session_config.get("password", ""))

    def save_config(self):
        """Save the current session configuration to the ConfigManager."""
        session_config = {
            "username": self.username_input.text().strip(),
            "password": self.password_input.text(),
        }
        self.config_manager.set_session_config(session_config)
        QMessageBox.information(
            self, "Sucesso", "Credenciais de sessão salvas com sucesso!"
        )
