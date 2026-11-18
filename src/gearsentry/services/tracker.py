from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from gearsentry.db.models import Product
from gearsentry.db.repository import ProductRepository
from gearsentry.schemas.product import ScrapedProduct


@dataclass(frozen=True)
class PriceChange:
    product: Product
    previous: Decimal | None
    current: Decimal

    @property
    def is_new(self) -> bool:
        return self.previous is None

    @property
    def delta_pct(self) -> Decimal | None:
        if self.previous is None or self.previous == 0:
            return None
        return ((self.current - self.previous) / self.previous * 100).quantize(Decimal("0.01"))

    @property
    def dropped(self) -> bool:
        return self.previous is not None and self.current < self.previous


def record_price(session: Session, scraped: ScrapedProduct) -> PriceChange:
    """Registra o preço e devolve a variação em relação ao último snapshot.

    Só grava novo snapshot quando o preço mudou (ou é a primeira vez),
    mantendo o histórico enxuto.
    """
    repo = ProductRepository(session)
    product = repo.get_or_create(scraped)
    last = repo.last_snapshot(product)
    previous = last.price if last else None

    if last is None or last.price != scraped.price:
        repo.add_snapshot(product, scraped)

    return PriceChange(product=product, previous=previous, current=scraped.price)
