import os
import sys
import asyncio
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox
import qasync
from src.core.config import ConfigManager
from src.core.session_manager import SessionManager
from src.utils.printer import PrinterManager
from src.frontend.inteface import Interface
from src.frontend.dialogs.login_dialog import LoginDialog


def load_stylesheet(app: QApplication) -> None:
    """Loads the global QSS stylesheet for the application."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    qss_path = os.path.join(base_dir, "src", "frontend", "theme.qss")

    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    else:
        print(f"Atenção: Arquivo de tema não encontrado em {qss_path}")


async def startup_logic(config_manager: ConfigManager, session_manager: SessionManager):
    """Lógica assíncrona executada antes da interface abrir."""
    while True:
        session_cfg = config_manager.get_session_config()

        if not session_cfg.get("username") or not session_cfg.get("password"):
            login_dialog = LoginDialog(config_manager)
            if login_dialog.exec() != QDialog.Accepted:
                sys.exit(0)

        if await session_manager.login():
            break
        else:
            QMessageBox.critical(
                None,
                "Erro de Autenticação",
                "Falha ao realizar login.\nVerifique seu usuário, senha e conexão com a internet.",
            )
            config_manager.set_session_config({"username": "", "password": ""})


def main() -> None:
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    load_stylesheet(app)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    config_manager = ConfigManager()
    session_manager = SessionManager(config_manager)
    printer_manager = PrinterManager()
    loop.run_until_complete(startup_logic(config_manager, session_manager))
    window = Interface(config_manager, printer_manager, session_manager)
    window.show()
    app.setQuitOnLastWindowClosed(True)
    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
