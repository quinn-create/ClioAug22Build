from clio_aug22_build.providers.clio.util import wrap_body


def test_wrap_plain_dict() -> None:
    assert wrap_body({"description": "DUI"}) == {"data": {"description": "DUI"}}


def test_already_wrapped_not_double_wrapped() -> None:
    body = {"data": {"description": "DUI"}}
    assert wrap_body(body) is body
    assert wrap_body(body) == {"data": {"description": "DUI"}}


def test_raw_bypasses_wrap() -> None:
    body = {"description": "DUI"}
    assert wrap_body(body, raw=True) == {"description": "DUI"}


def test_none_body() -> None:
    assert wrap_body(None) is None
    assert wrap_body(None, raw=True) is None
