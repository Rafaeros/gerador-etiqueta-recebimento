"""
Scraping with selenium
"""

import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


@dataclass
class OrderData:
    """Dataclass to represent an order"""

    code: str
    description: str
    qty: float
    unit_type: str
    order: str


@dataclass
class NFeData:
    """Dataclass to represent an NFe and generate a JSON file to generate labels"""

    nfe_number: str
    supplier: str
    orders: List[OrderData] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Converte a instância para um dicionário."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to json"""
        with open("nfe_data.json", "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=4)

        return json.dumps(self.to_dict(), ensure_ascii=False, indent=4)


class CargaMaquinaClient:
    """Client to interact with CargaMaquina"""

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    def _configure_chrome(self) -> Options:
        # Configurar as opções do Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Modo headless
        chrome_options.add_argument(
            "--disable-gpu"
        )  # Desativa GPU (recomendado no modo headless)
        chrome_options.add_argument("--no-sandbox")  # Aumenta a segurança
        chrome_options.add_argument(
            "--disable-dev-shm-usage"
        )  # Evita erros de memória em ambientes cloud

        return chrome_options

    def nfe_data_scraping(self) -> str:
        """Scraping NFE data"""
        driver = webdriver.Chrome()

        # Login
        driver.get("https://app.cargamaquina.com.br/site/login?c=31.1~78%2C8%5E56%2C8")

        username_input = driver.find_element(by=By.NAME, value="LoginForm[username]")
        username_input.send_keys(self.username)

        password_input = driver.find_element(by=By.NAME, value="LoginForm[password]")
        password_input.send_keys(self.password)

        login_button = driver.find_element(by=By.NAME, value="yt0")
        login_button.click()

        driver.get(
            "https://app.cargamaquina.com.br/compra?Compra%5Bnegociacao%5D=171910"
        )

        nfe_checkbox = driver.find_elements(
            by=By.XPATH, value='//*[@id="compraSelecionados_0"]'
        )
        nfe_checkbox[0].click()

        nfe_view = driver.find_element(by=By.XPATH, value='//*[@id="linkVisualizar"]')
        nfe_view.click()

        html: str = driver.page_source

        return html

    def get_data(self, content: str) -> None:
        """Get data from HTML and save it to a JSON format"""

        soup = BeautifulSoup(content, "html.parser")
        nfe_number = soup.find("input", {"id": "FaturamentoGrid_0_observacao"}).get(
            "value"
        )
        supplier = (
            soup.find("span", {"class": "select2-chosen"}).text.strip().split(" ")[0]
        )
        mp_table = soup.find_all("table")[1]
        orders = []

        trs = mp_table.find_all("tr")[1:]
        for tr in trs:
            code = tr.find_all("td")[3].text.strip()
            description = tr.find_all("td")[4].text.strip()
            qty, unit_type = tr.find_all("td")[7].text.strip().split(" ")
            order = tr.find_all("td")[17].text.strip()
            orders.append(
                OrderData(
                    code=code,
                    description=description,
                    qty=float(qty),
                    unit_type=unit_type,
                    order=order,
                )
            )
            nfe_data = NFeData(nfe_number=nfe_number, supplier=supplier, orders=orders)
            nfe_data.to_json()


if __name__ == "__main__":
    client = CargaMaquinaClient(username="your username", password="your password")
    print(client.get_data(client.nfe_data_scraping()))
