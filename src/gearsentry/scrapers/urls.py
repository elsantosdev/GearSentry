from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

# Parâmetros que identificam a oferta; todo o resto é rastreamento.
KEEP_PARAMS = {"pdp_filters"}


def normalize_url(url: str) -> str:
    """Remove fragmento e parâmetros de rastreamento, para que o mesmo produto
    tenha sempre a mesma URL no banco."""
    parts = urlparse(url.strip())
    query = urlencode([(k, v) for k, v in parse_qsl(parts.query) if k in KEEP_PARAMS])
    path = parts.path.rstrip("/") or "/"
    return urlunparse((parts.scheme.lower(), parts.netloc.lower(), path, "", query, ""))
