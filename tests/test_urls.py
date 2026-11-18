from gearsentry.scrapers.urls import normalize_url


def test_removes_fragment_and_tracking_params():
    url = "https://www.terabyteshop.com.br/produto/1/x?utm_source=a&tracking_id=9#frag"
    assert normalize_url(url) == "https://www.terabyteshop.com.br/produto/1/x"


def test_keeps_offer_identifier():
    url = "https://www.mercadolivre.com.br/p/MLB1?pdp_filters=item_id%3AMLB2&sid=search"
    assert normalize_url(url) == (
        "https://www.mercadolivre.com.br/p/MLB1?pdp_filters=item_id%3AMLB2"
    )


def test_same_product_same_url():
    a = normalize_url("https://Loja.com/p/1/?a=1")
    b = normalize_url("https://loja.com/p/1#x")
    assert a == b
