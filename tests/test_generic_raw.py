import pytest

from clio_aug22_build.providers.clio.util import PathSafetyError, nest_id, normalize_clio_path, resource_from_path


API = "https://app.clio.com/api/v4"


def test_relative_path() -> None:
    url, extra = normalize_clio_path("/contacts", API)
    assert url == "https://app.clio.com/api/v4/contacts"
    assert extra == {}


def test_strips_api_prefix() -> None:
    url, _ = normalize_clio_path("/api/v4/matters/1", API)
    assert url == "https://app.clio.com/api/v4/matters/1"


def test_rejects_off_host() -> None:
    with pytest.raises(PathSafetyError):
        normalize_clio_path("https://evil.test/steal", API)


def test_rejects_traversal() -> None:
    with pytest.raises(PathSafetyError):
        normalize_clio_path("/contacts/../secrets", API)


def test_rejects_protocol_relative() -> None:
    with pytest.raises(PathSafetyError):
        normalize_clio_path("//evil.test/x", API)


def test_same_host_url_ok() -> None:
    url, extra = normalize_clio_path(
        "https://app.clio.com/api/v4/contacts?page_token=abc", API
    )
    assert url.endswith("/contacts")
    assert extra.get("page_token") == "abc"


def test_resource_from_path() -> None:
    assert resource_from_path("/api/v4/contacts/12") == "contacts"
    assert resource_from_path("/users/who_am_i") == "users/who_am_i"


def test_nest_id() -> None:
    assert nest_id(9) == {"id": 9}
    assert nest_id(None) is None
