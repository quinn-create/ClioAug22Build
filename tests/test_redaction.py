from clio_aug22_build.logging_setup import redact


def test_redacts_bearer() -> None:
    text = redact("Authorization: Bearer abcdefghijklmnop")
    assert "abcdefghijklmnop" not in text
    assert "[REDACTED]" in text


def test_redacts_assigned_secrets() -> None:
    text = redact("refresh_token=super-secret-value client_secret=shh")
    assert "super-secret-value" not in text
    assert "shh" not in text


def test_redacts_json_tokens() -> None:
    text = redact('{"access_token": "WjR8HLsecret", "expires_in": 2592000}')
    assert "WjR8HLsecret" not in text
    assert "2592000" in text
