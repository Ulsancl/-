import socket

import pytest

from autogpt_server.blocks.rss import ReadRSSFeedBlock


def test_validate_rss_url_rejects_localhost():
    with pytest.raises(ValueError, match="host is not allowed"):
        ReadRSSFeedBlock.validate_rss_url("http://localhost/rss")


def test_validate_rss_url_rejects_private_ip():
    with pytest.raises(ValueError, match="host is not allowed"):
        ReadRSSFeedBlock.validate_rss_url("http://127.0.0.1/rss")


def test_validate_rss_url_rejects_private_dns_resolution(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(None, None, None, None, ("10.0.0.1", 0))],
    )

    with pytest.raises(ValueError, match="host is not allowed"):
        ReadRSSFeedBlock.validate_rss_url("https://example.com/rss")


def test_validate_rss_url_accepts_global_dns_resolution(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(None, None, None, None, ("93.184.216.34", 0))],
    )

    assert (
        ReadRSSFeedBlock.validate_rss_url("https://example.com/rss")
        == "https://example.com/rss"
    )
