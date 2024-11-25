"""
Module to Scrape data from CargaMaquina
"""

import json
import asyncio
from datetime import datetime
import logging
from typing import Optional, List, Dict, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import aiohttp
from bs4 import BeautifulSoup

@dataclass
class OrderData:
    """Dataclass to represent an order"""
    pedido: str
    fornecedor: str
    codigo: str
    material: str
    quantidade_total: float
    quantidade_recebida: float
    quantidade_pendente: float

    def to_dict(self) -> dict:
        """Convert OrderData to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'OrderData':
        """Create OrderData from dictionary"""
        return cls(**data)


class CargaMaquinaClient:
    """Client to interact with CargaMaquina"""
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = "https://app.cargamaquina.com.br"
        self.logger = logging.getLogger(__name__)

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def login(self) -> bool:
        """
        Login to CargaMaquina
        Returns True if login was successful
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        login_url = f"{self.base_url}/site/login?c=31.1~78%2C8%5E56%2C8"
        login_payload = {
            "LoginForm[username]": self.username,
            "LoginForm[password]": self.password,
            "LoginForm[codigoConexao]": "31.1~78,8^56,8",
            "yt0": "Entrar"
        }

        try:
            async with self.session.post(url=login_url, data=login_payload) as response:
                print("Login successful")
                return response.status == 200
        except Exception as e:
            self.logger.error("Login failed: %s", str(e))
            return False

    def _parse_currency_to_float(self, value: str) -> float:
        """Convert currency string to float"""
        try:
            cleaned = value.replace('R$', '').replace(
                '.', '').replace(',', '.').strip()
            return float(cleaned)
        except (ValueError, AttributeError):
            return 0.0

    def _parse_quantity_to_float(self, value: str) -> float:
        """Convert quantity string to float"""
        try:
            cleaned = value.replace(',', '.').strip()
            return float(cleaned)
        except (ValueError, AttributeError):
            return 0.0

    def _parse_table_row(self, row) -> Optional[OrderData]:
        """Parse a single table row into OrderData"""
        try:
            cells = row.find_all('td')
            return OrderData(
                pedido=cells[0].text.strip(),
                fornecedor=cells[3].text.strip().split(' ')[0],
                codigo=cells[5].text.strip(),
                material=cells[6].text.strip(),
                quantidade_recebida=self._parse_quantity_to_float(cells[9].text),
                quantidade_pendente=self._parse_quantity_to_float(cells[10].text),
                quantidade_total=self._parse_quantity_to_float(cells[11].text),
            )
        except Exception as e:
            self.logger.error("Error parsing row: %s", str(e))
            return None

    def parse_orders_html(self, html_content: str) -> List[OrderData]:
        """Parse HTML content and extract orders data"""
        soup = BeautifulSoup(html_content, 'html.parser')
        trs = soup.find_all("tr")

        orders = []
        for row in trs[1:]:
            order_data = self._parse_table_row(row)
            if order_data:
                orders.append(order_data)

        return orders

    def orders_to_dict_list(self, orders: List[OrderData]) -> List[Dict]:
        """Convert list of OrderData to list of dictionaries"""
        return [order.to_dict() for order in orders]

    def orders_to_json(self, orders: List[OrderData], indent: int = 2) -> str:
        """Convert list of OrderData to JSON string"""
        return json.dumps(self.orders_to_dict_list(orders),
                          ensure_ascii=False,
                          indent=indent)

    def save_orders_json(self, orders: List[OrderData],
                         filepath: Union[str, Path],
                         indent: int = 2) -> None:
        """Save orders to JSON file"""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.orders_to_dict_list(orders), f,
                      ensure_ascii=False,
                      indent=indent)

    def load_orders_json(self, filepath: Union[str, Path]) -> List[OrderData]:
        """Load orders from JSON file"""
        filepath = Path(filepath)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [OrderData.from_dict(item) for item in data]
        except Exception as e:
            self.logger.error("Error loading JSON file: %s", str(e))
            return []

    async def get_orders_data(self) -> Optional[List[OrderData]]:
        """Get orders data from CargaMaquina and parse it"""
        if not self.session:
            self.logger.error("No active session. Please login first.")
            return None

        orders_url = f"{self.base_url}/relatorio/compra/renderGridExportacaoEntregasPendentes"
        params = {
            'RelatorioEntregasPendentes[referencia]': 'ENT',
            'RelatorioEntregasPendentes[previsaoInicio]': '',
            'RelatorioEntregasPendentes[previsaoFim]': '',
            'RelatorioEntregasPendentes[fornecedorId]': '',
            'idNovoMaterialsel2Material': '',
            'novoMaterialsel2Material': '',
            'txtNomeMaterialModalmodalIncluirMaterialSimplificadosel2Material': '',
            'unidadeMedidaId': '',
            'servicoIdModalmodalIncluirMaterialSimplificadosel2Material': '',
            'RelatorioEntregasPendentes[materialId]': '',
            'RelatorioEntregasPendentes[tipoFrete]': '9',
        }

        try:
            async with self.session.get(url=orders_url, params=params) as response:
                if response.status == 200:
                    print("GET SUCCESS")
                    html_content = await response.text()
                    return self.parse_orders_html(html_content)
                else:
                    self.logger.error("Failed to get orders data. Status: %d", response.status)
                    return None
        except Exception as e:
            self.logger.error("Error fetching orders data: %s", str(e))
            return None


async def periodic_fetch(interval_seconds: int = 300):
    """
    Periodically fetch and parse orders data
    :param interval_seconds: Time between requests in seconds (default 5 minutes)
    """
    async with CargaMaquinaClient(username="your_username", password="your_password") as client:
        if not await client.login():
            raise Exception("Failed to login")

        # Create data directory if it doesn't exist
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)

        while True:
            try:
                orders = await client.get_orders_data()
                if orders:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

                    # Save raw orders data
                    json_path = data_dir / f"orders_{timestamp}.json"
                    client.save_orders_json(orders, json_path)
                    print(f"Saved orders data to {json_path}")

                await asyncio.sleep(interval_seconds)

            except Exception as e:
                print(f"Error during fetch: {str(e)}")
                if not await client.login():
                    print("Failed to re-login, waiting before retry...")
                await asyncio.sleep(60)

# Example usage
if __name__ == "__main__":
    async def main():
        """Main function"""
        async with CargaMaquinaClient(username="your username", password="your password") as client:
            if await client.login():
                orders = await client.get_orders_data()
                if orders:
                    # Salvar dados brutos
                    client.save_orders_json(orders, "pedidos.json")
    asyncio.run(main())
