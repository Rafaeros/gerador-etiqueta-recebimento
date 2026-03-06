from dataclasses import asdict, dataclass, field
import json
from typing import Dict, List
from pydantic import BaseModel, Field


class Material(BaseModel):
    """Pydantic model to represent a pending material"""

    creation_date: str
    code: str
    op_number: str
    product: str
    pending_qty: float
    service_type: str


class PendingMaterials(BaseModel):
    """Pydantic model to represent a list of pending materials"""

    pending_materials: List[Material] = Field(default_factory=list)

    def to_dict(self) -> dict:
        """Returns the dictionary representation of the model"""
        return self.model_dump()

    def save_to_json(self) -> dict:
        """Saves to file and returns the dictionary"""
        data_dict = self.model_dump()

        with open("./tmp/pending_materials.json", "w", encoding="utf-8") as f:
            json.dump(data_dict, f, ensure_ascii=False, indent=4)

        return data_dict


class OrderData(BaseModel):
    """Pydantic model to represent an order"""
    nfe: int
    supplier: str
    address: str
    order: int
    code: str
    description: str
    qty: float
    qty_total: float
    unit_type: str


class NFeData(BaseModel):
    """Pydantic model to represent an NFe and generate a JSON file"""

    date: str
    orders: List[OrderData] = Field(default_factory=list)
    pending_materials: List[Dict] = Field(default_factory=list)

    def save_to_json(self, nfe_number: str) -> str:
        """Saves to file and returns the JSON string"""
        json_str = self.model_dump_json(indent=4)

        with open(f"./tmp/nfe_{nfe_number}.json", "w", encoding="utf-8") as f:
            f.write(json_str)

        return json_str
