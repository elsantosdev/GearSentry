from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal


class ProductCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str = Field(min_length=1)
    current_price: Decimal = Field(gt=0)
    url: str
    store: str
