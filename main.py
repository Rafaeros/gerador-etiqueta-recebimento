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
        print(f"Warning: Theme file not found at {qss_path}")


async def startup_logic(config_manager: ConfigManager, session_manager: SessionManager) -> bool:
    """
    Asynchronous logic executed before opening the main interface.
    Returns True if successfully connected to the remote system, False otherwise.
    """
    session_cfg = config_manager.get_session_config()

    # Prompt for credentials if none are saved
    if not session_cfg.get("username") or not session_cfg.get("password"):
        login_dialog = LoginDialog(config_manager)
        if login_dialog.exec() != QDialog.Accepted:
            sys.exit(0)

    # Attempt to authenticate
    is_connected = await session_manager.login()
    
    # Display offline warning if authentication fails
    if not is_connected:
        QMessageBox.warning(
            None,
            "Modo Offline",
            "Não foi possível conectar ao sistema CargaMáquina (Credenciais inválidas ou sem internet).\n\n"
            "O aplicativo será iniciado em Modo Offline. Você ainda poderá usar a aba 'Manual' e acessar as 'Configurações'."
        )
        
    return is_connected


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

    # Execute startup logic and capture connection status
    is_connected = loop.run_until_complete(startup_logic(config_manager, session_manager))
    
    # Initialize the interface with the connection status
    window = Interface(config_manager, printer_manager, session_manager, is_connected)
    window.show()
    
    app.setQuitOnLastWindowClosed(True)
    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()