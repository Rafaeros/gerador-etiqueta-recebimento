import logging
from typing import List
from bs4 import BeautifulSoup
from datetime import datetime as dt
from src.models.schemas import OrderData, Material, PendingMaterials, NFeData
from src.core.session_manager import SessionManager

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class RequestsScraper:

    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager

    async def extract_all_data(self, nfe_number: str, init_date: str, end_date: str) -> NFeData:
        """
        Extracts all data from the NFe page and saves it to a JSON file.
        """
        orders_list = await self.extract_nfe_data(nfe_number, init_date, end_date)
        if not orders_list:
            logging.warning("Nenhuma ordem encontrada para a NFe %s.", nfe_number)
            return NFeData(date=dt.now().strftime("%d/%m/%y"))

        codes = [order.code for order in orders_list]
        pending_data_dict = await self.extract_pending_materials(codes, init_date, end_date)
        pending_list = pending_data_dict.get("pending_materials", [])
        pending_list = sorted(
            pending_list,
            key=lambda x: dt.strptime(x["creation_date"], "%d/%m/%y"),
        )

        nfe_data = NFeData(
            date=dt.now().strftime("%d/%m/%y"),
            orders=orders_list,
            pending_materials=pending_list
        )

        if nfe_data.pending_materials:
            for pending_material in nfe_data.pending_materials:
                for order in nfe_data.orders:
                    if pending_material["code"] == order.code:
                        logging.info("Cruzamento - Order qty: %s | Pending qty: %s", order.qty, pending_material["pending_qty"])
                        if order.qty == 0:
                            pending_material["pending_qty"] = 0
                            continue

                        if pending_material["pending_qty"] > order.qty:
                            pending_material["pending_qty"] = order.qty
                            order.qty = 0.0
                        else:
                            order.qty -= pending_material["pending_qty"]

            nfe_data.pending_materials = [
                pm for pm in nfe_data.pending_materials if pm["pending_qty"] > 0
            ]
        
        nfe_data.orders = [
            order for order in nfe_data.orders if order.qty > 0
        ]

        nfe_data.save_to_json(nfe_number)
        logging.info("Processo concluído. Arquivo salvo em ./tmp/data_%s.json", nfe_number)

        return nfe_data

    async def extract_nfe_data(
        self, nfe_number: str, init_date: str, end_date: str
    ) -> List[OrderData]:

        session = self.session_manager.session
        if not session:
            logging.error("Sessão HTTP não inicializada. Realize o login primeiro.")
            return []

        endpoint = f"{self.session_manager.base_url}/relatorio/compra/renderGridExportacaoPedidosCompraPeriodo"
        headers = {
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{self.session_manager.base_url}/relatorio/compra/pedidosCompraPeriodo",
        }

        params = [
            ("RelatorioPedidosCompra[dataInicio]", init_date),
            ("RelatorioPedidosCompra[dataFim]", end_date),
            ("RelatorioPedidosCompra[tipoPeriodo]", "CRI"),
            ("idNovoMaterialsel2Material", ""),
            ("novoMaterialsel2Material", ""),
            ("txtNomeMaterialModalmodalIncluirMaterialSimplificadosel2Material", ""),
            ("unidadeMedidaId", ""),
            ("servicoIdModalmodalIncluirMaterialSimplificadosel2Material", ""),
            ("RelatorioPedidosCompra[materialId]", ""),
            ("RelatorioPedidosCompra[compradorId]", ""),
            ("tituloBack", "Solicitante da RC"),
            ("[hidenExceto]", "0"),
            ("RelatorioPedidosCompra[solicitanteRCId]", ""),
            ("tituloBack", ""),
            ("[hidenExceto]", "0"),
            ("RelatorioPedidosCompra[numeroRC]", ""),
        ]

        try:
            logging.info(f"Buscando relatórios de {init_date} até {end_date}...")
            async with session.get(
                endpoint, headers=headers, params=params
            ) as response:
                response.raise_for_status()
                html_content = await response.text()

                return self._parse_nfe_data_table(html_content, nfe_number)

        except Exception as e:
            logging.exception("Falha ao capturar o relatório: %s", e)
            return []

    def _parse_nfe_data_table(self, html: str, nfe_number: str) -> List[OrderData]:
            """
            Parse the HTML content to extract order data.
            """
            soup = BeautifulSoup(html, "html.parser")
            aggregated_data = {}
            trs = soup.find_all("tr")

            for tr in trs:
                tds = tr.find_all("td")
                if len(tds) >= 24:
                    extracted_nfe = tds[24].get_text(strip=True)
                    if extracted_nfe == nfe_number:
                        order_str = tds[4].get_text(strip=True)
                        supplier = tds[9].get_text(strip=True).split(" ")[0]
                        code = tds[11].get_text(strip=True)
                        description = tds[12].get_text(strip=True)
                        unit_type = tds[13].get_text(strip=True)
                        qty_str = (
                            tds[15].get_text(strip=True).replace(".", "").replace(",", ".")
                        )
                        
                        try:
                            nfe_val = int(extracted_nfe)
                            qty_val = float(qty_str)
                        except ValueError as e:
                            logging.warning(
                                "Falha ao converter tipos da NFE %s na linha de pedido %s: %s",
                                extracted_nfe,
                                order_str,
                                e,
                            )
                            continue
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
                                "address": "",
                                "order": order_str,
                                "code": code,
                                "description": description,
                                "qty": qty_val,
                                "qty_total": qty_val,
                                "unit_type": unit_type,
                            }

            data: List[OrderData] = [OrderData(**item) for item in aggregated_data.values()]
            logging.info(
                "Extração concluída. %d registros aglomerados em OrderData para a NFE %s.",
                len(data),
                nfe_number,
            )
            print(data)
            return data

    async def extract_pending_materials(
        self, 
        nfe_material_code: List[str], 
        init_date: str = "01/10/2025", 
        end_date: str = ""
    ) -> List[Material]:
        """
        Extracts pending materials from the HTML response, applying filters for unit type and NFe codes.
        """
        session = self.session_manager.session
        if not session:
            logging.error("Sessão HTTP não inicializada. Realize o login primeiro.")
            return []

        if not end_date:
            end_date = f"31/12/{dt.now().year}"

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
            ("Pedido[_inicioCriacao]", init_date),
            ("Pedido[_fimCriacao]", end_date),
            ("pageSize", "20"), 
        ]

        try:
            logging.info("Buscando relatório de materiais pendentes...")
            async with session.get(endpoint, headers=headers, params=params) as response:
                response.raise_for_status()
                html_content = await response.text()

                return self._parse_pending_materials(html_content, nfe_material_code)

        except Exception as e:
            logging.exception("Falha ao capturar os materiais pendentes: %s", e)
            return []

    def _parse_pending_materials(self, html: str, nfe_material_code: List[str]) -> dict:
        """
        Parse the HTML content to extract pending materials.
        """
        soup = BeautifulSoup(html, "html.parser")
        data: List[Material] = []
        trs = soup.find_all("tr")[1:]

        for tr in trs:
            tds = tr.find_all("td")
            if len(tds) >= 10:
                raw_date = tds[0].get_text(strip=True)
                service_type = tds[1].get_text(strip=True)
                code = tds[2].get_text(strip=True)

                if code not in nfe_material_code:
                    continue

                qty_full_text = tds[9].get_text(strip=True).split(" ")
                pending_qty_str = qty_full_text[0]
                unit_type = qty_full_text[-1]

                if unit_type.lower() == "mt":
                    continue

                op_number = str(tds[4].get_text(strip=True))
                product = tds[6].get_text(strip=True)
                try:
                    creation_date = dt.strptime(raw_date, "%d/%m/%y").strftime("%d/%m/%y")
                except ValueError:
                    creation_date = raw_date
                try:
                    if "." in pending_qty_str:
                        pending_qty_str = pending_qty_str.replace(".", "")
                    pending_qty_str = pending_qty_str.replace(",", ".")
                    pending_qty_val = float(pending_qty_str)
                except ValueError as e:
                    logging.warning("Falha ao converter a qtde '%s' do código %s: %s", pending_qty_str, code, e)
                    continue

                material_data = Material(
                    creation_date=creation_date,
                    code=code,
                    op_number=op_number,
                    product=product,
                    pending_qty=pending_qty_val,
                    service_type=service_type
                )
                
                data.append(material_data)
                
        pending_materials = PendingMaterials(pending_materials=data)
        logging.info("Extração concluída. %d materiais capturados após filtros.", len(pending_materials.pending_materials))
        data: dict = pending_materials.to_dict()
        return data