from clio_aug22_build.providers.clio.util import extract_page_token, hours_to_seconds, paging_from_payload, resolve_quantity_seconds


def test_extract_page_token_from_query() -> None:
    url = "https://app.clio.com/api/v4/contacts?fields=id&page_token=abc123&order=id(asc)"
    assert extract_page_token(url) == "abc123"


def test_extract_page_token_falls_back_to_url() -> None:
    url = "https://app.clio.com/api/v4/contacts?fields=id&cursor=xyz"
    assert extract_page_token(url) == url


def test_extract_page_token_none() -> None:
    assert extract_page_token(None) is None


def test_paging_from_payload() -> None:
    payload = {
        "data": [],
        "meta": {"paging": {"next": "https://app.clio.com/api/v4/contacts?page_token=n2"}},
    }
    paging = paging_from_payload(payload)
    assert paging["has_next"] is True
    assert paging["next_page_token"] == "n2"


def test_hours_to_seconds() -> None:
    assert hours_to_seconds(1) == 3600
    assert hours_to_seconds(1.5) == 5400
    assert hours_to_seconds(0.1) == 360


def test_quantity_seconds_wins() -> None:
    assert resolve_quantity_seconds(2, 99) == 99
    assert resolve_quantity_seconds(0.5, None) == 1800
