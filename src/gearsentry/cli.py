import asyncio
import sys

import typer
from loguru import logger

from gearsentry.db.models import Product
from gearsentry.db.repository import ProductRepository
from gearsentry.db.session import get_engine, session_scope
from gearsentry.schemas.product import ScrapedProduct
from gearsentry.scrapers.base import ScraperError
from gearsentry.scrapers.registry import get_scraper
from gearsentry.scrapers.urls import normalize_url
from gearsentry.services.tracker import PriceChange, record_price

app = typer.Typer(help="GearSentry: monitor de preços de periféricos.", no_args_is_help=True)

MAX_CONCURRENCY = 3


def _configure_logging(verbose: bool) -> None:
    logger.remove()
    logger.add(sys.stderr, level="DEBUG" if verbose else "WARNING")


async def _scrape_all(urls: list[str]) -> list[ScrapedProduct | ScraperError]:
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

    async def one(url: str) -> ScrapedProduct | ScraperError:
        async with semaphore:
            try:
                return await get_scraper(url).scrape(url)
            except ScraperError as exc:
                return exc

    return await asyncio.gather(*(one(u) for u in urls))


def _format_change(change: PriceChange) -> str:
    name = change.product.name[:60]
    if change.is_new:
        return f"+ {name}: R$ {change.current} (primeiro registro)"
    if change.delta_pct == 0:
        return f"= {name}: R$ {change.current} (sem mudança)"
    arrow = "↓" if change.dropped else "↑"
    return f"{arrow} {name}: R$ {change.previous} → R$ {change.current} ({change.delta_pct}%)"


def _run(urls: list[str]) -> int:
    """Raspa, persiste e imprime. Retorna a quantidade de falhas."""
    engine = get_engine()
    results = asyncio.run(_scrape_all(urls))
    failures = 0
    with session_scope(engine) as session:
        for url, result in zip(urls, results, strict=True):
            if isinstance(result, ScraperError):
                failures += 1
                typer.secho(f"! {url}: {result}", fg=typer.colors.RED, err=True)
                continue
            typer.echo(_format_change(record_price(session, result)))
    return failures


@app.callback()
def main(verbose: bool = typer.Option(False, "--verbose", "-v")) -> None:
    _configure_logging(verbose)


@app.command()
def track(url: str) -> None:
    """Começa a monitorar um produto (raspa agora e registra o preço inicial)."""
    if _run([normalize_url(url)]):
        raise typer.Exit(code=1)


@app.command()
def scrape() -> None:
    """Raspa todos os produtos monitorados e registra variações."""
    engine = get_engine()
    with session_scope(engine) as session:
        urls = [p.url for p in ProductRepository(session).list_all()]
    if not urls:
        typer.echo("Nenhum produto monitorado. Use: gearsentry track <url>")
        return
    if _run(urls):
        raise typer.Exit(code=1)


@app.command(name="list")
def list_products() -> None:
    """Lista os produtos monitorados."""
    engine = get_engine()
    with session_scope(engine) as session:
        repo = ProductRepository(session)
        for product in repo.list_all():
            last = repo.last_snapshot(product)
            price = f"R$ {last.price}" if last else "—"
            typer.echo(f"[{product.id}] {product.store:<13} {price:>12}  {product.name[:60]}")


@app.command()
def history(product_id: int) -> None:
    """Mostra o histórico de preços de um produto."""
    engine = get_engine()
    with session_scope(engine) as session:
        product = session.get(Product, product_id)
        if product is None:
            typer.secho("Produto não encontrado.", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        typer.echo(product.name)
        for snap in product.snapshots:
            typer.echo(f"  {snap.scraped_at:%Y-%m-%d %H:%M}  R$ {snap.price}")
