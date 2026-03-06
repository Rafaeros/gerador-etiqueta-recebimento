from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
)
from src.core.config import ConfigManager


class LoginDialog(QDialog):
    """
    Dialog for initial login configuration.
    Prompts the user to enter their username and password, which are then saved to the configuration file.
    This dialog is shown when the application detects that no valid session credentials are present.
    """

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager

        self.setWindowTitle("Configuração Inicial - Login")
        self.setFixedSize(300, 200)
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Defina seu Usuário:"))
        self.input_login = QLineEdit()
        layout.addWidget(self.input_login)

        layout.addWidget(QLabel("Defina sua Senha:"))
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.input_password)

        self.btn_save = QPushButton("Salvar e Continuar")
        self.btn_save.setObjectName("primary")
        self.btn_save.clicked.connect(self.handle_save)
        layout.addWidget(self.btn_save)

    def handle_save(self) -> None:
        username = self.input_login.text().strip()
        password = self.input_password.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Aviso", "Por favor, preencha todos os campos.")
            return

        self.config_manager.set_session_config(
            {"username": username, "password": password}
        )
        self.accept()
