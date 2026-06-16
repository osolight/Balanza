# models.py

from pydantic import BaseModel
from typing import List

class Producto(BaseModel):
    name: str
    product_qty: float
    qty_bruto: float
    qty_tara: float
    net_weight: float
    price_unit: float

class TicketData(BaseModel):
    company_name: str
    company_rif: str
    purchase: str
    product_name: str
    product_rif: str
    date: str  # también puedes usar datetime
    products: List[Producto]
    net_total: float
    ip: str
    ticket_type: str
