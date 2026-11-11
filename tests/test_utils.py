from decimal import Decimal

import pytest
from bs4 import BeautifulSoup

from src.scrapers.exceptions import ParseError
from src.scrapers.utils import (
    find_json_value,
    find_next_data_price,
    first_text,
    load_json_lenient,
    parse_price,
)


@pytest.mark.parametrize(
    "raw, esperado",
    [
        ("R$ 1.999,99", Decimal("1999.99")),
        ("R$ 999,90", Decimal("999.90")),
        ("À vista R$ 12.345,00 no pix", Decimal("12345.00")),
        ("R$ 0,00", Decimal("0.00")),
        ("1,299.00", Decimal("1299.00")),  # formato americano
        ("1.999", Decimal("1999")),  # ponto + 3 dígitos = milhar
        ("1.234.567", Decimal("1234567")),
        ("199.9", Decimal("199.9")),  # ponto decimal (JSON em texto)
        ("1299", Decimal("1299")),
        (1299, Decimal("1299")),
        (199.9, Decimal("199.9")),
    ],
)
def test_parse_price(raw, esperado):
    assert parse_price(raw) == esperado


@pytest.mark.parametrize("raw", ["Indisponível", "", True, float("nan"), float("inf")])
def test_parse_price_invalido(raw):
    with pytest.raises(ParseError):
        parse_price(raw)


def test_parse_price_regressao_json_float_nao_vira_10x():
    # Bug original: str(199.9) passava pelo parser de texto, que removia o ponto.
    assert parse_price(199.9) == Decimal("199.9")
    assert parse_price("199.9") == Decimal("199.9")


class TestFindJsonValue:
    def test_acha_chave_aninhada_em_lista(self):
        data = {"props": {"items": [{"x": 1}, {"price": 49.9}]}}
        assert find_json_value(data, ("price",)) == 49.9

    def test_ignora_chave_case_insensitive(self):
        assert find_json_value({"Price": "10"}, ("price",)) == "10"

    def test_chave_do_mesmo_nivel_tem_prioridade_sobre_aninhada(self):
        data = {"shipping": {"price": 12}, "price": 199.9}
        assert find_json_value(data, ("price",)) == 199.9

    def test_ignora_chaves_nao_listadas(self):
        # Regressão: "value" (frete, etc.) não pode ser tratado como preço.
        data = {"shipping": {"value": 12}, "price": 199.9}
        assert find_json_value(data, ("price",)) == 199.9

    @pytest.mark.parametrize("valor", [True, None, "", "grátis", {}, []])
    def test_ignora_valores_que_nao_parecem_preco(self, valor):
        assert find_json_value({"price": valor}, ("price",)) is None

    def test_json_sem_a_chave(self):
        assert find_json_value({"a": [1, 2, {"b": 3}]}, ("price",)) is None


class TestLoadJsonLenient:
    def test_json_puro(self):
        assert load_json_lenient('{"a": 1}') == {"a": 1}

    def test_json_dentro_de_javascript(self):
        assert load_json_lenient('window.__DATA__ = {"a": 1};') == {"a": 1}

    def test_invalido(self):
        assert load_json_lenient("console.log('oi')") is None


class TestFirstText:
    def test_pula_elemento_vazio_e_usa_o_proximo(self):
        soup = BeautifulSoup('<p class="a"></p><p class="b">R$ 10,00</p>', "html.parser")
        assert first_text(soup, (".a", ".b")) == "R$ 10,00"

    def test_require_digit_ignora_texto_sem_numero(self):
        soup = BeautifulSoup('<p class="a">Indisponível</p><p class="b">R$ 10,00</p>', "html.parser")
        assert first_text(soup, (".a", ".b"), require_digit=True) == "R$ 10,00"
        assert first_text(soup, (".a", ".b")) == "Indisponível"

    def test_le_content_de_meta(self):
        soup = BeautifulSoup('<meta property="og:price:amount" content="199.9">', "html.parser")
        assert first_text(soup, ("meta[property='og:price:amount']",)) == "199.9"

    def test_nenhum_seletor_casa(self):
        assert first_text(BeautifulSoup("<p></p>", "html.parser"), (".x",)) is None


def test_find_next_data_price():
    html = '<script id="__NEXT_DATA__" type="application/json">{"a": {"price": 59.9}}</script>'
    soup = BeautifulSoup(html, "html.parser")
    assert find_next_data_price(soup, ("price",)) == 59.9


def test_find_next_data_price_sem_script():
    assert find_next_data_price(BeautifulSoup("<p></p>", "html.parser"), ("price",)) is None
