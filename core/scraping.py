"""
Scraping with selenium and requests
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import List, Dict
from datetime import datetime as dt
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@dataclass
class Material:
    """Dataclass to represent a pending material"""

    creation_date: str
    code: str
    op_number: str
    product: str
    pending_qty: float


@dataclass
class PendingMaterials:
    """Dataclass to represent a list of pending materials"""

    pending_materials: List[Material] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert the istance to a dictionary"""
        return asdict(self)

    def to_json(self) -> dict:
        """Convert to json"""
        with open("./tmp/pending_materials.json", "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=4)

        return self.to_dict()


@dataclass
class OrderData:
    """Dataclass to represent an order"""

    address: str
    order: int
    code: str
    description: str
    qty: float
    qty_total: float
    unit_type: str


@dataclass
class NFeData:
    """Dataclass to represent an NFe and generate a JSON file to generate labels"""

    date: str
    nfe_number: int
    supplier_name: str
    orders: List[OrderData] = field(default_factory=list)
    pending_materials: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert the istance to a dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to json"""
        with open("./tmp/nfe_data.json", "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=4)

        return json.dumps(self.to_dict(), ensure_ascii=False, indent=4)


class CargaMaquinaClient:
    """Client to interact with CargaMaquina"""

    today = dt.now()
    username: str
    password: str

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.driver = webdriver.Chrome()
        self.requests_cookies: dict = {}
        self.selenium_cookies: dict = {}
        self._initialize_client()

    def _initialize_client(self):
        try:
            self.login()
        except WebDriverException as e:
            print(f"Error: {e}")

    def _configure_chrome(self) -> Options:
        """Configure chrome options to run in headless mode."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        return chrome_options

    def _save_cookies(self) -> Dict:
        """Save cookies to a JSON file"""
        self.selenium_cookies = self.driver.get_cookies()

        with open("./tmp/cookies.json", "w", encoding="utf-8") as f:
            json.dump(self.selenium_cookies, f, ensure_ascii=False, indent=4)

        self.requests_cookies = {
            cookie["name"]: cookie["value"] for cookie in self.selenium_cookies
        }
        with open("./tmp/requests_cookies.json", "w", encoding="utf-8") as f:
            json.dump(self.requests_cookies, f, ensure_ascii=False, indent=4)

    def _load_cookies(self):
        """Load cookies from a JSON file"""
        if "cookies.json" in os.listdir():
            with open("./tmp/cookies.json", "r", encoding="utf-8") as file:
                self.selenium_cookies = json.load(file)
        else:
            raise FileNotFoundError
        if "requests_cookies.json" in os.listdir():
            with open("./tmp/requests_cookies.json", "r", encoding="utf-8") as file:
                self.requests_cookies = json.load(file)
        else:
            raise FileNotFoundError


    def close(self):
        self.driver.quit()

    def login(self):
        """Login to carga maquina and get cookies for requests"""
        try:
            self.driver.get(
                "https://app.cargamaquina.com.br/site/login?c=31.1~78%2C8%5E56%2C8"
            )

            try:
                username_input = self.driver.find_element(
                    by=By.NAME, value="LoginForm[username]"
                )

                password_input = self.driver.find_element(
                    by=By.NAME, value="LoginForm[password]"
                )

                username_input.send_keys(self.username)
                password_input.send_keys(self.password)

            except NoSuchElementException as e:
                print(f"Campos de login ou senha não encontrados. {e}")

            login_button = self.driver.find_element(by=By.NAME, value="yt0")
            login_button.click()
            self._save_cookies()
        except TimeoutException as e:
            print(f"Timeout: {e}")
        except WebDriverException as e:
            print(f"Error: {e}")

    def nfe_data_scraping(self, negociation_id: str) -> None:
        """Scraping NFE data"""
        try:
            self.driver.get(
                f"https://app.cargamaquina.com.br/compra?Compra%5Bnegociacao%5D={negociation_id}"
            )
            nfe_checkbox = WebDriverWait(self.driver, 20).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, '//*[@id="compraSelecionados_0"]')
                )
            )
            nfe_checkbox[0].click()

            nfe_view = self.driver.find_element(
                by=By.XPATH, value='//*[@id="linkVisualizar"]'
            )
            nfe_view.click()

            html: str = self.driver.page_source
            self.get_nfe_data(html)

        except TimeoutException as e:
            print(f"Timeout: {e}")
        except WebDriverException as e:
            print(f"Error: {e}")

    def get_nfe_data(self, html: str) -> str:
        """Get data from HTML and save it to a JSON format"""
        soup = BeautifulSoup(html, "html.parser")
        nfe_number: int = int(
            soup.find("input", {"id": "FaturamentoGrid_0_observacao"})
            .get("value")
            .split("-")[-1]
            .strip()
        )
        supplier_name: str = (
            soup.find("span", {"class": "select2-chosen"}).text.strip().split(" ")[0]
        )
        mp_table = soup.find_all("table")[1]
        orders: List[OrderData] = []
        trs = mp_table.find_all("tr")[1:]
        for tr in trs:
            order: int = tr.find_all("td")[3].text.strip()
            address: str = tr.find_all("td")[4].text.strip()
            code: str = tr.find_all("td")[5].text.strip()
            description: str = tr.find_all("td")[6].text.strip()
            qty: float = tr.find_all("td")[8].text.strip().split(" ")[0]
            unit_type: str = tr.find_all("td")[8].text.strip().split(" ")[-1].upper()
            orders.append(
                OrderData(
                    address=address,
                    order=order,
                    code=code,
                    description=description,
                    qty=float(qty),
                    qty_total=float(qty),
                    unit_type=unit_type,
                )
            )
        nfe_data: NFeData = NFeData(
            date=dt.now().strftime("%d/%m/%Y"),
            nfe_number=nfe_number,
            supplier_name=supplier_name,
            orders=orders,
        )
        # Getting pending materials by codes in Nfe data scraping and sorting by crescent date.
        codes: list[str] = [order.code for order in nfe_data.orders]
        pending_materials: dict = self.get_requested_materials(codes)
        nfe_data.pending_materials = pending_materials["pending_materials"]
        nfe_data.pending_materials = sorted(
            nfe_data.pending_materials,
            key=lambda x: dt.strptime(x["creation_date"], "%d/%m/%y"),
        )

        print(nfe_data.to_json())

        if nfe_data.pending_materials:
            for pending_material in nfe_data.pending_materials:
                for order in nfe_data.orders:
                    if pending_material["code"] == order.code:
                        print("Order qty:", order.qty)
                        print("Pending material qty:", pending_material["pending_qty"])
                        # Order qty validation
                        if order.qty == 0:
                            pending_material["pending_qty"] = 0

                        # Pending material qty validation
                        if pending_material["pending_qty"] > order.qty:
                            while pending_material["pending_qty"] > order.qty:
                                pending_material["pending_qty"] -= 1
                            order.qty -= pending_material["pending_qty"]
                        elif pending_material["pending_qty"] < order.qty:
                            order.qty -= pending_material["pending_qty"]
                        elif pending_material["pending_qty"] == order.qty:
                            order.qty -= pending_material["pending_qty"]

            nfe_data.pending_materials = [pending_material for pending_material in nfe_data.pending_materials if pending_material["pending_qty"] > 0]
        for order in nfe_data.orders:
            if order.qty == 0:
                nfe_data.orders.remove(order)

        nfe_data.to_json()
        return nfe_data

    def get_requested_materials(self, nfe_material_code: List[str]):
        """Get the data of pending materials in production orders on CargaMaquina"""
        params: dict[str, str] = {
            "Pedido[_nomeMaterial]": "",
            "Pedido[_solicitante]": "",
            "Pedido[status_id]": "",
            "Pedido[situacao]": "TODAS",
            "Pedido[_qtdeFornecida]": "Parcialmente",
            "Pedido[_inicioCriacao]": f"01/01/{self.today.year}",
            "Pedido[_fimCriacao]": f"25/12/{self.today.year}",
            "pageSize": "20",
        }

        response = requests.get(
            "https://app.cargamaquina.com.br/pedido/exportarPedidoFaltaMP",
            params=params,
            cookies=self.requests_cookies,
            timeout=20,
        )

        if not response.ok:
            print(f"Error to get pending_materials status_code: {response.status_code}")
            return None
        try:
            soup = BeautifulSoup(response.content, "html.parser")

            materials: List[Material] = []
            trs: list = soup.find_all("tr")[1:]
            for tr in trs:
                creation_date: dt = dt.strptime(
                    tr.find_all("td")[0].text.strip(), "%d/%m/%y"
                )
                code: str = tr.find_all("td")[1].text.strip()
                op_number: str = str(tr.find_all("td")[3].text.strip())
                product: str = tr.find_all("td")[5].text.strip()
                pending_qty: str | float = (
                    tr.find_all("td")[8].text.strip().split(" ")[0]
                )
                unit_type: str = tr.find_all("td")[8].text.strip().split(" ")[-1]

                if (creation_date.year < self.today.year) or (unit_type == "mt"):
                    continue

                if "." in pending_qty:
                    pending_qty = float(pending_qty.replace(".", ""))

                if code not in nfe_material_code:
                    continue

                pending_qty = float(pending_qty)
                materials.append(
                    Material(
                        creation_date=creation_date.strftime("%d/%m/%y"),
                        code=code,
                        op_number=op_number,
                        product=product,
                        pending_qty=pending_qty,
                    )
                )
            pending_materials: PendingMaterials = PendingMaterials(
                pending_materials=materials
            )
            data: dict = pending_materials.to_dict()
            return data

        except ValueError as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    client = CargaMaquinaClient(username="your username", password="your password")
    client.nfe_data_scraping(negociation_id="your negociation id")
