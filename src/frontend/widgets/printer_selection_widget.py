from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QComboBox,
    QLabel,
    QPushButton,
    QMessageBox,
)
from src.utils.printer import PrinterManager
from src.core.config import ConfigManager


class PrinterSelectionWidget(QWidget):
    """Widget for selecting and saving the default system printer."""

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
        self.load_config()

    def setup_ui(self):
        """Sets up the user interface layout and components."""
        layout = QVBoxLayout(self)

        printer_label = QLabel("Selecione a impressora:")
        layout.addWidget(printer_label)
        self.printer_combo_box = QComboBox()
        self.printer_combo_box.addItems(self.printer_manager.list_printers())
        layout.addWidget(self.printer_combo_box)
        self.save_default_printer_btn = QPushButton("Salvar impressora padrão")
        self.save_default_printer_btn.setObjectName("primary")
        self.save_default_printer_btn.clicked.connect(self.on_save_default_printer)
        layout.addWidget(self.save_default_printer_btn)
        layout.addStretch()

    def load_config(self):
        """Loads the saved printer from JSON and selects it in the ComboBox."""
        saved_printer = self.config_manager.get("printer_name", "")
        if saved_printer:
            # Search for the text in the list. If found (>= 0), set it as the current selection.
            index = self.printer_combo_box.findText(saved_printer)
            if index >= 0:
                self.printer_combo_box.setCurrentIndex(index)

    def on_save_default_printer(self):
        """Saves the selected printer to the JSON file when the button is clicked."""
        selected_printer = self.printer_combo_box.currentText()

        if not selected_printer:
            QMessageBox.warning(
                self, "Aviso", "Nenhuma impressora disponível para salvar."
            )
            return

        self.config_manager.set("printer_name", selected_printer)

        QMessageBox.information(
            self,
            "Sucesso",
            f"Impressora '{selected_printer}' salva como padrão com sucesso!",
        )
