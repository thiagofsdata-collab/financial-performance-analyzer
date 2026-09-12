from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict


DreLine = Literal[
    "Receita Bruta",
    "Deducoes da Receita",
    "COGS",
    "Opex",
    "Resultado Financeiro",
    "Impostos",
]

Company = Literal["Company A", "Company B"]
BusinessUnit = Literal["Retail", "Wholesale", "E-commerce"]


class TransactionRecord(BaseModel):
    """Data contract for a single financial transaction.

    Validates structure and types only (not cross-record business rules,
    e.g. amount sign vs dre_line — that belongs to warehouse-layer tests).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    transaction_id: str
    date: date
    company: Company
    business_unit: BusinessUnit
    cost_center: str
    account_code: str
    account_name: str
    dre_line: DreLine
    amount: Decimal
