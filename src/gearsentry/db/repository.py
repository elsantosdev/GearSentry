from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from gearsentry.db.models import PriceSnapshot, Product
from gearsentry.schemas.product import ScrapedProduct


def to_cents(value: Decimal) -> int:
    return int((value * 100).to_integral_value())


class ProductRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_url(self, url: str) -> Product | None:
        return self.session.scalar(select(Product).where(Product.url == url))

    def list_all(self) -> list[Product]:
        return list(self.session.scalars(select(Product).order_by(Product.id)))

    def get_or_create(self, scraped: ScrapedProduct) -> Product:
        product = self.get_by_url(scraped.url)
        if product is None:
            product = Product(url=scraped.url, store=scraped.store, name=scraped.title)
            self.session.add(product)
            self.session.flush()
        return product

    def last_snapshot(self, product: Product) -> PriceSnapshot | None:
        return self.session.scalar(
            select(PriceSnapshot)
            .where(PriceSnapshot.product_id == product.id)
            .order_by(PriceSnapshot.scraped_at.desc(), PriceSnapshot.id.desc())
            .limit(1)
        )

    def add_snapshot(self, product: Product, scraped: ScrapedProduct) -> PriceSnapshot:
        snapshot = PriceSnapshot(
            product_id=product.id,
            price_cents=to_cents(scraped.price),
            currency=scraped.currency,
        )
        self.session.add(snapshot)
        self.session.flush()
        return snapshot
