from datetime import datetime
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QFrame,
    QStackedWidget,
    QGridLayout,
    QMessageBox,
    QSpinBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


def get_fifo_color(date_str: str) -> str:
    """Returns a color based on the month of the date string."""
    try:
        month = int(date_str.split("/")[1])
    except:
        month = datetime.now().month

    colors = {
        1: "#8B4513",  # Marrom
        2: "#FF00FF",  # Magenta
        3: "#FFFFFF",  # Branco
        4: "#F5F5DC",  # Bege
        5: "#FFA500",  # Laranja
        6: "#C8A2C8",  # Lilás
        7: "#90EE90",  # Verde Claro
        8: "#ADD8E6",  # Azul Claro
        9: "#006400",  # Verde Escuro
        10: "#FFFF00",  # Amarelo
        11: "#FFC0CB",  # Rosa
        12: "#D3D3D3",  # Cinza Claro
    }
    return colors.get(month, "#FFFFFF")


class StockLabelEditor(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedSize(550, 450)
        self.setup_ui()

    def update_bg_color(self, hex_color: str):
        self.setStyleSheet(
            f"""
            StockLabelEditor {{ background-color: {hex_color}; border: 2px solid #0f172a; border-radius: 5px; }}
            QLineEdit {{ border: 1px dashed #cbd5e1; background-color: rgba(255, 255, 255, 0.9); padding: 6px; font-size: 16px; font-weight: bold; color: #0f172a;}}
            QLineEdit:focus {{ border: 2px solid #7609e8; background-color: white; }}
        """
        )

    def setup_ui(self):
        layout = QGridLayout(self)

        self.input_nfe = QLineEdit()
        self.input_nfe.setPlaceholderText("NF (ex: 12345)")

        self.input_address = QLineEdit()
        self.input_address.setPlaceholderText("Endereço (ex: A-12)")

        layout.addWidget(self.input_nfe, 0, 0)
        layout.addWidget(self.input_address, 0, 1)

        self.input_supplier = QLineEdit()
        self.input_supplier.setPlaceholderText("FORNECEDOR")
        font_large = QFont("Arial", 18, QFont.Bold)
        self.input_supplier.setFont(font_large)
        layout.addWidget(self.input_supplier, 1, 0, 1, 2)

        self.input_code = QLineEdit()
        self.input_code.setPlaceholderText("CÓDIGO (ex: CNFAT12CZ)")
        self.input_code.setStyleSheet(
            "background-color: #0f172a; color: white; border: none; padding: 10px;"
        )
        self.input_code.setFont(font_large)
        layout.addWidget(self.input_code, 2, 0, 1, 2)

        self.input_desc = QLineEdit()
        self.input_desc.setPlaceholderText("Descrição do material...")
        layout.addWidget(self.input_desc, 3, 0, 1, 2)

        self.input_qty = QLineEdit()
        self.input_qty.setPlaceholderText("Qtd (ex: 100)")

        self.input_qty_total = QLineEdit()
        self.input_qty_total.setPlaceholderText("Lote Total (ex: 500)")

        layout.addWidget(self.input_qty, 4, 0)
        layout.addWidget(self.input_qty_total, 4, 1)

    def get_data(self) -> dict:
        """Collect data from the editor"""
        return {
            "type": "stock",
            "nfe": self.input_nfe.text(),
            "address": self.input_address.text().upper(),
            "supplier": self.input_supplier.text().upper(),
            "code": self.input_code.text().upper(),
            "description": self.input_desc.text(),
            "qty": self.input_qty.text(),
            "qty_total": self.input_qty_total.text(),
        }

    def clear_fields(self):
        self.input_nfe.clear()
        self.input_address.clear()
        self.input_supplier.clear()
        self.input_code.clear()
        self.input_desc.clear()
        self.input_qty.clear()
        self.input_qty_total.clear()


class PendingLabelEditor(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedSize(550, 450)
        self.setup_ui()

    def update_bg_color(self, hex_color: str):
        self.setStyleSheet(
            f"""
            PendingLabelEditor {{ background-color: {hex_color}; border: 2px solid #0f172a; border-radius: 5px; }}
            QLineEdit {{ border: 1px solid #cbd5e1; background-color: rgba(255, 255, 255, 0.95); color: #0f172a; padding: 8px; border-radius: 4px; font-size: 16px; font-weight: bold;}}
            QLineEdit:focus {{ border: 2px solid #7609e8; background-color: white; }}
        """
        )

    def setup_ui(self):
        layout = QVBoxLayout(self)
        top_layout = QHBoxLayout()
        self.input_nfe = QLineEdit()
        self.input_nfe.setPlaceholderText("NF 12345")
        self.input_service = QLineEdit()
        self.input_service.setText("Venda")
        top_layout.addWidget(self.input_nfe)
        top_layout.addWidget(self.input_service)
        layout.addLayout(top_layout)

        font_large = QFont("Arial", 16, QFont.Bold)
        self.input_op = QLineEdit()
        self.input_op.setPlaceholderText("OP-0000000")
        self.input_op.setFont(font_large)
        layout.addWidget(self.input_op)

        self.input_product = QLineEdit()
        self.input_product.setPlaceholderText("PRODUTO")
        self.input_product.setFont(font_large)
        layout.addWidget(self.input_product)

        self.input_code = QLineEdit()
        self.input_code.setPlaceholderText("CÓDIGO MATERIAL")
        self.input_code.setFont(font_large)
        layout.addWidget(self.input_code)

        self.input_qty = QLineEdit()
        self.input_qty.setPlaceholderText("QUANTIDADE: 10")
        layout.addWidget(self.input_qty)

    def get_data(self) -> dict:
        """Collect data from the editor"""
        return {
            "type": "pending",
            "nfe": self.input_nfe.text(),
            "service_type": self.input_service.text(),
            "op_number": self.input_op.text(),
            "product": self.input_product.text(),
            "code": self.input_code.text().upper(),
            "qty": self.input_qty.text(),
        }

    def clear_fields(self):
        self.input_nfe.clear()
        self.input_service.setText("Venda")
        self.input_op.clear()
        self.input_product.clear()
        self.input_code.clear()
        self.input_qty.clear()


class NFELabelEditor(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedSize(550, 450)
        self.setup_ui()

    def update_bg_color(self, hex_color: str):
        self.setStyleSheet(
            f"""
            NFELabelEditor {{ background-color: {hex_color}; border: 2px solid #0f172a; border-radius: 5px; }}
            QLineEdit {{ border: 1px dashed #cbd5e1; background-color: rgba(255, 255, 255, 0.9); padding: 10px; color: #0f172a; }}
            QLineEdit:focus {{ border: 2px solid #7609e8; background-color: white; }}
        """
        )

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addStretch()

        self.input_nfe = QLineEdit()
        self.input_nfe.setPlaceholderText("Digite a NFE")
        self.input_nfe.setAlignment(Qt.AlignCenter)
        font_huge = QFont("Arial", 48, QFont.Bold)
        self.input_nfe.setFont(font_huge)

        layout.addWidget(self.input_nfe)

        lbl_counter = QLabel("1 / 10")
        lbl_counter.setAlignment(Qt.AlignCenter)
        lbl_counter.setStyleSheet(
            "color: #0f172a; font-size: 48px; font-weight: bold; margin-top: 10px; background: transparent; border: none;"
        )
        layout.addWidget(lbl_counter)

        layout.addStretch()

    def get_data(self) -> dict:
        """Collect data from the editor"""
        return {"type": "nfe", "nfe": self.input_nfe.text()}

    def clear_fields(self):
        self.input_nfe.clear()


class LabelTab(QWidget):
    def __init__(self, config_manager, printer_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.printer_manager = printer_manager
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        control_layout = QHBoxLayout()
        lbl_date = QLabel("Data FIFO:")
        lbl_date.setStyleSheet("font-weight: bold; color: #475569;")
        self.input_global_date = QLineEdit()
        self.input_global_date.setFixedWidth(100)
        self.input_global_date.setText(datetime.now().strftime("%d/%m/%y"))
        self.input_global_date.textChanged.connect(self.apply_fifo_color)

        lbl_select = QLabel("Modelo:")
        lbl_select.setStyleSheet("font-weight: bold; color: #475569;")
        self.combo_type = QComboBox()
        self.combo_type.setMinimumWidth(200)
        self.combo_type.addItems(
            ["Etiqueta de Estoque", "Etiqueta de Falta", "Etiqueta de NFE (Múltiplas)"]
        )
        self.combo_type.currentIndexChanged.connect(self.change_label_type)

        lbl_qty = QLabel("Cópias:")
        lbl_qty.setStyleSheet("font-weight: bold; color: #475569;")
        self.spin_qty = QSpinBox()
        self.spin_qty.setMinimumWidth(70)
        self.spin_qty.setRange(1, 1000)
        self.spin_qty.setValue(1)

        control_layout.addWidget(lbl_date)
        control_layout.addWidget(self.input_global_date)
        control_layout.addSpacing(20)
        control_layout.addWidget(lbl_select)
        control_layout.addWidget(self.combo_type)
        control_layout.addSpacing(20)
        control_layout.addWidget(lbl_qty)
        control_layout.addWidget(self.spin_qty)
        control_layout.addStretch()

        stage_layout = QHBoxLayout()
        self.stacked_widget = QStackedWidget()

        self.stock_editor = StockLabelEditor()
        self.pending_editor = PendingLabelEditor()
        self.nfe_editor = NFELabelEditor()

        self.stacked_widget.addWidget(self.stock_editor)
        self.stacked_widget.addWidget(self.pending_editor)
        self.stacked_widget.addWidget(self.nfe_editor)

        stage_layout.addStretch()
        stage_layout.addWidget(self.stacked_widget)
        stage_layout.addStretch()

        action_layout = QHBoxLayout()

        self.btn_clear = QPushButton("Limpar Campos")
        self.btn_clear.setMinimumHeight(45)
        self.btn_clear.clicked.connect(self.clear_current_editor)

        self.btn_print = QPushButton("Gerar e Imprimir (Enter)")
        self.btn_print.setMinimumHeight(45)
        self.btn_print.setMinimumWidth(250)
        self.btn_print.setObjectName("primary")
        self.btn_print.clicked.connect(self.handle_print)

        action_layout.addStretch()
        action_layout.addWidget(self.btn_clear)
        action_layout.addSpacing(10)
        action_layout.addWidget(self.btn_print)

        main_layout.addLayout(control_layout)
        main_layout.addSpacing(20)
        main_layout.addLayout(stage_layout)
        main_layout.addStretch()
        main_layout.addLayout(action_layout)

        self.apply_fifo_color()
        self.stock_editor.input_qty_total.returnPressed.connect(self.handle_print)
        self.pending_editor.input_qty.returnPressed.connect(self.handle_print)
        self.nfe_editor.input_nfe.returnPressed.connect(self.handle_print)

    def apply_fifo_color(self):
        """Apply color to all editors based on the FIFO date"""
        color = get_fifo_color(self.input_global_date.text())
        self.stock_editor.update_bg_color(color)
        self.pending_editor.update_bg_color(color)
        self.nfe_editor.update_bg_color(color)

    def change_label_type(self, index: int):
        self.stacked_widget.setCurrentIndex(index)

    def clear_current_editor(self):
        """Clear inputs only from the label that is currently visible"""
        current_editor = self.stacked_widget.currentWidget()
        current_editor.clear_fields()

    def handle_print(self):
        current_editor = self.stacked_widget.currentWidget()
        if isinstance(current_editor, StockLabelEditor):
            data = current_editor.get_data()
        elif isinstance(current_editor, PendingLabelEditor):
            data = current_editor.get_data()
        elif isinstance(current_editor, NFELabelEditor):
            data = current_editor.get_data()

        data["date"] = self.input_global_date.text()
        data["print_qty"] = self.spin_qty.value()

        if data["type"] == "nfe" and not data.get("nfe"):
            QMessageBox.warning(self, "Aviso", "O campo 'NFE' é obrigatório!")
            return
        elif data["type"] != "nfe" and not data.get("code"):
            QMessageBox.warning(self, "Aviso", "O campo 'Código' é obrigatório!")
            return

        from src.utils.labels import generate_manual_labels

        self.btn_print.setEnabled(False)
        self.btn_print.setText("Gerando...")

        try:
            generated_files = generate_manual_labels(data, "s")

            target_printer = self.config_manager.get("printer_name", "")
            if not target_printer:
                target_printer = self.printer_manager.get_default_printer()

            if not target_printer:
                QMessageBox.warning(
                    self,
                    "Impressora não configurada",
                    "Nenhuma impressora encontrada nas configurações.",
                )
                return

            print_success = 0
            for file_path in generated_files:
                if self.printer_manager.print_document(
                    file_path, printer_name=target_printer
                ):
                    print_success += 1

            QMessageBox.information(
                self,
                "Sucesso",
                f"{print_success} etiquetas enviadas para {target_printer}.",
            )

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao imprimir:\n{str(e)}")
        finally:
            self.btn_print.setEnabled(True)
            self.btn_print.setText("Gerar e Imprimir (Enter)")
