from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ScrapedProduct(BaseModel):
    """Resultado validado de uma raspagem, independente da loja."""

    model_config = ConfigDict(str_strip_whitespace=True, frozen=True)

    url: str
    store: str
    title: str = Field(min_length=1)
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = "BRL"
