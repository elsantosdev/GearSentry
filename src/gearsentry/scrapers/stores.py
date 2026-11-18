from gearsentry.scrapers.jsonld import JsonLdScraper


class TerabyteScraper(JsonLdScraper):
    store = "terabyte"
    domains = ("terabyteshop.com.br",)


class MercadoLivreScraper(JsonLdScraper):
    store = "mercadolivre"
    domains = ("mercadolivre.com.br",)
