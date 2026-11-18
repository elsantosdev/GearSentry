from decimal import Decimal

from gearsentry.db.repository import ProductRepository
from gearsentry.schemas.product import ScrapedProduct
from gearsentry.services.tracker import record_price


def _scraped(price: str) -> ScrapedProduct:
    return ScrapedProduct(
        url="https://x.com/p", store="terabyte", title="Headset", price=Decimal(price)
    )


def test_first_record_is_new(session):
    change = record_price(session, _scraped("100.00"))
    assert change.is_new and change.previous is None


def test_unchanged_price_does_not_add_snapshot(session):
    record_price(session, _scraped("100.00"))
    change = record_price(session, _scraped("100.00"))
    product = ProductRepository(session).list_all()[0]
    assert len(product.snapshots) == 1
    assert change.delta_pct == Decimal("0.00") and not change.dropped


def test_price_drop_detected(session):
    record_price(session, _scraped("200.00"))
    change = record_price(session, _scraped("150.00"))
    assert change.dropped
    assert change.delta_pct == Decimal("-25.00")
    assert len(change.product.snapshots) == 2
    assert ProductRepository(session).last_snapshot(change.product).price == Decimal("150")
