from decimal import Decimal

import pytest
from pydantic import ValidationError

from gearsentry.schemas.product import ScrapedProduct


def test_rejects_non_positive_price():
    with pytest.raises(ValidationError):
        ScrapedProduct(url="u", store="s", title="t", price=Decimal("0"))


def test_rejects_blank_title():
    with pytest.raises(ValidationError):
        ScrapedProduct(url="u", store="s", title="   ", price=Decimal("10"))
