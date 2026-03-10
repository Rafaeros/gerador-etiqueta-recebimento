import re
import logging
from typing import List
from bs4 import BeautifulSoup
from datetime import datetime as dt
from playwright.async_api import async_playwright
from src.models.schemas import OrderData, Material, PendingMaterials, NFeData
from src.core.session_manager import SessionManager

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class RequestsScraper:
    """
    Scraper responsible for extracting NFe data and pending materials using
    both aiohttp for raw requests and Playwright for complex DOM interactions.
    """

    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager

    async def extract_all_data(
        self, negociation_id: str, init_date: str, end_date: str
    ) -> NFeData:
        """
        Orchestrates the extraction of the NFe data using Playwright, matches it
        with pending materials, processes the quantities, and saves the JSON.
        """
        # 1. Extract NFe data using Playwright headless browser
        orders_list = await self.extract_nfe_data_playwright(negociation_id)

        if not orders_list:
            logging.warning("No orders found for negotiation ID %s.", negociation_id)
            return NFeData(
                date=dt.now().strftime("%d/%m/%y"),
                nfe_number=0,
                supplier_name="",
                orders=[],
            )

        # Get the real NFe number and supplier from the first parsed order
        real_nfe_number = orders_list[0].nfe
        supplier = orders_list[0].supplier

        # 2. Extract pending materials using the existing aiohttp method
        codes = [order.code for order in orders_list]
        pending_data_dict = await self.extract_pending_materials(codes)
        pending_list = pending_data_dict.get("pending_materials", [])

        # Sort pending materials by creation date
        pending_list = sorted(
            pending_list,
            key=lambda x: dt.strptime(x["creation_date"], "%d/%m/%y"),
        )

        nfe_data = NFeData(
            date=dt.now().strftime("%d/%m/%y"),
            nfe_number=real_nfe_number,
            supplier_name=supplier,
            orders=orders_list,
            pending_materials=pending_list,
        )

        # 3. Validation and quantity deduction logic
        if nfe_data.pending_materials:
            for pending_material in nfe_data.pending_materials:
                for order in nfe_data.orders:
                    if pending_material["code"] == order.code:
                        logging.info(
                            "Matching - Order qty: %s | Pending qty: %s",
                            order.qty,
                            pending_material["pending_qty"],
                        )
                        if order.qty == 0:
                            pending_material["pending_qty"] = 0
                            continue

                        if pending_material["pending_qty"] > order.qty:
                            pending_material["pending_qty"] = order.qty
                            order.qty = 0.0
                        else:
                            order.qty -= pending_material["pending_qty"]

            # Keep only pending materials that still have quantity > 0
            nfe_data.pending_materials = [
                pm for pm in nfe_data.pending_materials if pm["pending_qty"] > 0
            ]

        # We no longer filter out orders with qty == 0 so they can be shown in the UI
        # and their pending materials can still be printed.

        # Save to JSON
        nfe_data.save_to_json(str(real_nfe_number))
        logging.info(
            "Process completed. File saved as ./tmp/data_%s.json", real_nfe_number
        )

        return nfe_data

    async def extract_nfe_data_playwright(self, negociation_id: str) -> List[OrderData]:
        """
        Navigates using Playwright, injecting the authenticated cookies from aiohttp.
        Currently set to headless=False so you can see the browser actions.
        """

        if not self.session_manager.session:
            logging.error("HTTP Session not initialized. Please login first.")
            return []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()

            # --- Cookie Injection ---
            cookies = []
            for cookie in self.session_manager.session.cookie_jar:
                cookies.append(
                    {
                        "name": cookie.key,
                        "value": cookie.value,
                        "domain": cookie["domain"] or ".cargamaquina.com.br",
                        "path": cookie["path"] or "/",
                    }
                )
            await context.add_cookies(cookies)

            page = await context.new_page()

            try:
                logging.info("Navigating to negotiation %s...", negociation_id)
                url = f"{self.session_manager.base_url}/compra?Compra%5Bnegociacao%5D={negociation_id}"
                await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                checkbox_locator = page.locator('//*[@id="compraSelecionados_0"]')
                await checkbox_locator.wait_for(state="visible", timeout=20000)
                await checkbox_locator.click()

                # Click the view button
                await page.locator('//*[@id="linkVisualizar"]').click()
                # pois é um input type="hidden" e nunca ficará "visible".
                await page.locator("input#FaturamentoGrid_0_observacao").wait_for(
                    state="attached", timeout=20000
                )

                # Extract the final rendered HTML
                html_content = await page.content()

                return self._parse_nfe_data_html(html_content)

            except Exception as e:
                logging.exception("Playwright navigation failed: %s", e)
                return []
            finally:
                # Opcional: Se quiser que a tela demore 2 segundinhos antes de fechar pra você conseguir ver o resultado final
                # import asyncio
                # await asyncio.sleep(2)
                await browser.close()

    def _parse_nfe_data_html(self, html: str) -> List[OrderData]:
        """
        Parses the HTML rendered by Playwright and aggregates duplicate material codes.
        """
        soup = BeautifulSoup(html, "html.parser")
        aggregated_data = {}

        try:
            # Extract the real NFe number from the input value
            raw_obs = soup.find("input", {"id": "FaturamentoGrid_0_observacao"}).get(
                "value"
            )
            nfe_val = int(raw_obs.split("-")[-1].strip())

            # Extract supplier name
            supplier = (
                soup.find("span", {"class": "select2-chosen"})
                .text.strip()
                .split(" ")[0]
            )

            # Target the correct table (index 1)
            mp_table = soup.find_all("table")[1]
            trs = mp_table.find_all("tr")[1:]
        except Exception as e:
            logging.error("Failed to find base elements in the extracted HTML: %s", e)
            return []

        for tr in trs:
            tds = tr.find_all("td")
            if len(tds) >= 9:
                order_str = tds[3].text.strip()
                address = tds[4].text.strip()
                code = tds[5].text.strip()
                description = tds[6].text.strip()
                qty_str = tds[8].text.strip().split(" ")[0]
                unit_type = tds[8].text.strip().split(" ")[-1].upper()

                try:
                    qty_val = float(qty_str.replace(".", "").replace(",", "."))
                except ValueError as e:
                    logging.warning(
                        "Failed to convert quantity '%s' for order %s: %s",
                        qty_str,
                        order_str,
                        e,
                    )
                    continue

                # AGGREGATION LOGIC (Sums quantities and concatenates orders for the same code)
                if code in aggregated_data:
                    aggregated_data[code]["qty"] += qty_val
                    aggregated_data[code]["qty_total"] += qty_val

                    existing_orders = aggregated_data[code]["order"].split("/")
                    if order_str not in existing_orders:
                        aggregated_data[code]["order"] += f"/{order_str}"
                else:
                    aggregated_data[code] = {
                        "nfe": nfe_val,
                        "supplier": supplier,
                        "address": address,
                        "order": order_str,
                        "code": code,
                        "description": description,
                        "qty": qty_val,
                        "qty_total": qty_val,
                        "unit_type": unit_type,
                    }

        # Convert dictionary values to a list of OrderData Pydantic models
        data: List[OrderData] = [OrderData(**item) for item in aggregated_data.values()]

        logging.info(
            "Extraction complete. %d aggregated records found for NFe %s.",
            len(data),
            nfe_val,
        )
        return data

    async def extract_pending_materials(
        self,
        nfe_material_code: List[str],
    ) -> dict:
        """
        Extracts pending materials from the HTML response, applying filters for unit type and NFe codes.
        (This method remains running efficiently on aiohttp without browser overhead)
        """
        session = self.session_manager.session
        if not session:
            logging.error("HTTP Session not initialized. Please login first.")
            return {}

        endpoint = f"{self.session_manager.base_url}/pedido/exportarPedidoFaltaMP"
        headers = {
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{self.session_manager.base_url}/pedido/pedidoFaltaMP",
        }

        params = [
            ("Pedido[_nomeMaterial]", ""),
            ("Pedido[_solicitante]", ""),
            ("Pedido[status_id]", ""),
            ("Pedido[situacao]", "TODAS"),
            ("Pedido[_qtdeFornecida]", "Parcialmente"),
            ("Pedido[_inicioCriacao]", "01/10/2025"),
            ("Pedido[_fimCriacao]", f"31/12/{dt.now().year}"),
            ("pageSize", "20"),
        ]

        try:
            logging.info("Fetching pending materials report via aiohttp...")
            async with session.get(
                endpoint, headers=headers, params=params
            ) as response:
                response.raise_for_status()
                html_content = await response.text()

                return self._parse_pending_materials(html_content, nfe_material_code)

        except Exception as e:
            logging.exception("Failed to capture pending materials: %s", e)
            return {}

    def _parse_pending_materials(self, html: str, nfe_material_code: List[str]) -> dict:
        """
        Parses the HTML content to extract pending materials using the exact old logic.
        """
        soup = BeautifulSoup(html, "html.parser")
        data: List[Material] = []
        trs = soup.find_all("tr")[1:]

        for tr in trs:
            tds = tr.find_all("td")
            if len(tds) >= 10:
                code = tds[2].text.strip()

                if code not in nfe_material_code:
                    continue

                raw_date = tds[0].text.strip()
                try:
                    creation_date = dt.strptime(raw_date, "%d/%m/%y").strftime(
                        "%d/%m/%y"
                    )
                except ValueError:
                    creation_date = raw_date

                service_type = tds[1].text.strip()
                op_number = str(tds[4].text.strip())
                product = tds[6].text.strip()

                qty_parts = tds[9].text.strip().split(" ")
                pending_qty_str = qty_parts[0]
                unit_type = qty_parts[-1].lower()

                if unit_type == "mt":
                    continue

                if "." in pending_qty_str:
                    pending_qty_str = pending_qty_str.replace(".", "")

                if "," in pending_qty_str:
                    pending_qty_str = pending_qty_str.replace(",", ".")

                try:
                    pending_qty_val = float(pending_qty_str)
                except ValueError as e:
                    logging.warning(
                        "Failed to convert quantity '%s' for code %s: %s",
                        pending_qty_str,
                        code,
                        e,
                    )
                    continue

                material_data = Material(
                    creation_date=creation_date,
                    code=code,
                    op_number=op_number,
                    product=product,
                    pending_qty=pending_qty_val,
                    service_type=service_type,
                )

                data.append(material_data)

        pending_materials = PendingMaterials(pending_materials=data)
        logging.info(
            "Extraction complete. %d pending materials captured after filtering.",
            len(pending_materials.pending_materials),
        )
        return pending_materials.to_dict()
