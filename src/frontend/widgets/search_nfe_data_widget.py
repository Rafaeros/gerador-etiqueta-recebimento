from qasync import asyncSlot
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
)
from datetime import datetime, timedelta
from src.core.session_manager import SessionManager
from src.core.config import ConfigManager
from src.core.scraper import RequestsScraper
from src.utils.labels import generate_nfe_labels
from src.utils.printer import PrinterManager


class SearchNfeDataWidget(QWidget):
    def __init__(
        self,
        session_manager: SessionManager,
        config_manager: ConfigManager,
        parent=None,
    ):
        super().__init__(parent)
        self.session_manager = session_manager
        self.config_manager = config_manager
        self.current_nfe_data = None
        self.setup_ui()

    def setup_ui(self) -> None:
        """Sets up the user interface layout and components."""
        layout = QVBoxLayout(self)
        # Header Title
        title_label = QLabel("📦 Recebimento de Materiais")
        title_label.setObjectName("title")
        layout.addWidget(title_label)

        # Search Container
        search_card = QFrame()
        search_card.setObjectName("card")
        search_card_layout = QVBoxLayout(search_card)
        search_card_layout.setContentsMargins(15, 15, 15, 15)

        search_input_layout = QHBoxLayout()
        self.id_label = QLabel("Compra ID:")
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("Digite o ID da compra (ex: 45678)...")
        self.id_input.setFixedWidth(300)

        self.btn_search = QPushButton("🔍 Buscar Dados")
        self.btn_search.setObjectName("primary")
        self.btn_search.setMinimumWidth(150)
        self.btn_search.clicked.connect(self.handle_search)
        self.id_input.returnPressed.connect(self.handle_search)

        search_input_layout.addWidget(self.id_label)
        search_input_layout.addWidget(self.id_input)
        search_input_layout.addWidget(self.btn_search)
        search_input_layout.addStretch()

        search_card_layout.addLayout(search_input_layout)
        layout.addWidget(search_card)

        # Table Section
        table_label = QLabel("📑 Materiais Encontrados")
        table_label.setStyleSheet(
            "font-weight: bold; color: #475569; margin-top: 10px;"
        )
        layout.addWidget(table_label)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(7)
        self.table_widget.setHorizontalHeaderLabels(
            [
                "Fornecedor",
                "Pedido",
                "Código",
                "Descrição",
                "Quantidade Total NFE",
                "Quantidade",
                "Quantidade de Faltas",
            ]
        )

        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Supplier
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Order
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Code
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Description
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Quantity Total
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Quantity
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Quantity Pending

        actions_layout = QHBoxLayout()

        self.btn_generate_labels = QPushButton("🖨️ Gerar e Imprimir Etiquetas")
        self.btn_generate_labels.setObjectName("primary")
        self.btn_generate_labels.setMinimumHeight(45)
        self.btn_generate_labels.setMinimumWidth(250)
        self.btn_generate_labels.setEnabled(False)
        self.btn_generate_labels.clicked.connect(self.handle_generate_labels)

        actions_layout.addStretch()
        actions_layout.addWidget(self.btn_generate_labels)

        layout.addWidget(self.table_widget)
        layout.addLayout(actions_layout)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

    @asyncSlot()
    async def handle_search(self) -> None:
        """Handles the search button click event using the authenticated session."""
        negociation_id = self.id_input.text().strip()

        if not negociation_id:
            QMessageBox.warning(self, "Aviso", "Por favor, insira o ID da compra.")
            return

        self.btn_search.setEnabled(False)
        self.btn_search.setText("Buscando...")
        self.table_widget.setRowCount(0)
        self.btn_generate_labels.setEnabled(False)

        try:
            now = datetime.now()
            init_date = (now - timedelta(days=30)).strftime("%d/%m/%Y")
            end_date = now.strftime("%d/%m/%Y")

            scraper = RequestsScraper(self.session_manager)
            response = await scraper.extract_all_data(
                negociation_id=negociation_id, init_date=init_date, end_date=end_date
            )
            self.current_nfe_data = response
            self.populate_table(response.orders)
            if response.orders:
                self.btn_generate_labels.setEnabled(True)
                QMessageBox.information(
                    self,
                    "Sucesso",
                    f"{len(response.orders)} itens carregados com sucesso!",
                )
            else:
                QMessageBox.information(
                    self, "Aviso", "Nenhum material encontrado para esta NFE."
                )

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao buscar dados: {e}")

        finally:
            self.btn_search.setEnabled(True)
            self.btn_search.setText("Buscar")

    def populate_table(self, orders: list) -> None:
        """Populates the table widget with the list of orders."""
        self.table_widget.setRowCount(len(orders))

        for row, order in enumerate(orders):
            item_supplier = QTableWidgetItem(str(order.supplier))
            item_order = QTableWidgetItem(str(order.order))
            item_code = QTableWidgetItem(str(order.code))
            description = QTableWidgetItem(str(order.description))
            item_qty_total = QTableWidgetItem(str(order.qty_total))
            item_qty = QTableWidgetItem(str(order.qty))
            try:
                left = int(order.qty_total) - int(order.qty)
            except (ValueError, TypeError):
                left = 0
            item_qty_pending = QTableWidgetItem(str(left))
            self.table_widget.setItem(row, 0, item_supplier)
            self.table_widget.setItem(row, 1, item_order)
            self.table_widget.setItem(row, 2, item_code)
            self.table_widget.setItem(row, 3, description)
            self.table_widget.setItem(row, 4, item_qty_total)
            self.table_widget.setItem(row, 5, item_qty)
            self.table_widget.setItem(row, 6, item_qty_pending)

    def clear_form(self) -> None:
        """Cleans the form inputs and resets the table and state."""
        self.id_input.clear()
        self.table_widget.setRowCount(0)
        self.current_nfe_data = None
        self.btn_generate_labels.setEnabled(False)

    def handle_generate_labels(self):
        """Generates labels by reading the cached model and sends them to the printer."""
        if not self.current_nfe_data:
            QMessageBox.warning(self, "Aviso", "Não há dados para gerar etiquetas.")
            return

        self.btn_generate_labels.setText("Gerando e Imprimindo...")
        self.btn_generate_labels.setEnabled(False)

        try:
            generated_files = generate_nfe_labels(
                self.current_nfe_data.orders[0].nfe, "s"
            )

            if not generated_files:
                QMessageBox.information(
                    self,
                    "Aviso",
                    "Não havia materiais pendentes ou pedidos válidos para gerar etiquetas.",
                )
                return

            printer_manager = PrinterManager()
            target_printer = self.config_manager.get("printer_name", "")
            if not target_printer:
                target_printer = printer_manager.get_default_printer()

            if not target_printer:
                QMessageBox.warning(
                    self,
                    "Impressora não configurada",
                    "Nenhuma impressora configurada. Por favor, vá até a aba 'Configurações' e selecione uma impressora.",
                )
                return

            print_success = 0
            for file_path in generated_files:
                if printer_manager.print_document(
                    file_path, printer_name=target_printer
                ):
                    print_success += 1

            if print_success == len(generated_files):
                QMessageBox.information(
                    self,
                    "Sucesso",
                    f"Foram gerados e enviados {print_success} arquivos para a impressora:\n{target_printer}",
                )
            else:
                failures = len(generated_files) - print_success
                QMessageBox.warning(
                    self,
                    "Atenção",
                    f"Processo finalizado, mas {failures} arquivo(s) falharam ao enviar para a impressora {target_printer}.",
                )

        except Exception as e:
            QMessageBox.critical(
                self, "Erro", f"Falha durante a geração/impressão:\n{str(e)}"
            )
            import logging

            logging.exception("Error generating or printing the labels")

        finally:
            self.btn_generate_labels.setText("Gerar Etiquetas")
            self.btn_generate_labels.setEnabled(True)
            self.clear_form()
