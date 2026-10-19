import pytest
from decimal import Decimal
from pydantic import ValidationError
from src.models import ProductBase


def test_valid_product_creation():
    # Assegura que uma instância de produto válida seja criada e que os campos sejam devidamente zerados.
    product = ProductBase(
        title="  Teclado Mecânico Redragon Kumara  ",
        store=" Kabum ",
        url="https://www.kabum.com.br/produto/12345",
        current_price=Decimal("199.90"),
        original_price=Decimal("299.90"),
    )

    assert product.title == "Teclado Mecânico Redragon Kumara"
    assert product.store == "Kabum"
    assert product.current_price == Decimal("199.90")
    assert product.discount_percentage == 33.34
    assert product.in_stock is True


def test_invalid_price_raises_validation_error():
    # A garantia é que preços que sejam zero ou inferiores, acionam um erro de validação estrita.
    with pytest.raises(ValidationError):
        ProductBase(
            title="Mouse Gamer Logitech",
            store="Amazon",
            url="https://www.amazon.com.br/dp/B00000",
            current_price=Decimal("-10.00"),  # Preço inválido
        )


def test_discount_calculation_without_original_price():
    # Certifica-se de que valores de preço abaixo ou iguais a zero gerem um aviso de validação rigoroso.
    product = ProductBase(
        title="Headset HyperX Cloud II",
        store="Pichau",
        url="https://www.pichau.com.br/headset-123",
        current_price=Decimal("450.00"),
    )

    assert product.discount_percentage == 0.0
