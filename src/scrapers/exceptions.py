class ScraperError(Exception):
    """
    Erro base de qualquer scraper.
    """


class StoreRequestError(ScraperError):
    """
    Falha de rede/timeout ao acessar a loja.
    """


class ProductNotFound(ScraperError):
    """
    A loja respondeu 404: a URL não existe mais.
    """


class BlockedByStore(ScraperError):
    """
    A loja bloqueou a requisição (403/429, anti-bot).
    """


class ParseError(ScraperError):
    """
    O HTML veio, mas título ou preço não foram encontrados/são inválidos.
    Normalmente significa que o layout da loja mudou.
    """


class ProductUnavailable(ScraperError):
    """
    Produto sem estoque ou com preço zerado.
    """
