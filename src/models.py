from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator


class ProductBase(BaseModel):
    # Modelo base para validação de periféricos recolhidos.

    title: str = Field(..., min_length=3, description="Nome do periférico")
    store: str = Field(..., min_length=2,
                       description="Nome da loja (Ex: Kabum, Pichau, Terabyte ...)")
    url: HttpUrl = Field(...,
                         description="Link direto para a página do produto")
    current_price: Decimal = Field(..., gt=0, description="Preço atual")
    original_price: Optional[Decimal] = Field(
        default=None, gt=0, description="Preço sem desconto (se houver)")
    in_stock: bool = Field(
        default=True, description="Disponibilidade de estoque")
    category: str = Field(default="peripherals",
                          description="Categoria (ex: teclado, mouse, headset)")

    # Garante que strings não venham com espaços no HTML
    @field_validator("title", "store")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        return value.strip()

    # Calcula o percentual de desconto real se tiver preco original
    @property
    def discount_percentage(self) -> float:
        if not self.original_price or self.original_price <= self.current_price:
            return 0.0

        discount = ((self.original_price - self.current_price) /
                    self.original_price) * 100
        return round(float(discount), 2)


class PriceSnapshot(BaseModel):
    # Armazenamento provisório de custos para compilar o histórico no banco de dados.
    product_url: HttpUrl
    price: Decimal = Field(..., gt=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
