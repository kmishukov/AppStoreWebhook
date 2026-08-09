import pytest

from app.tg.config import Configuration


def test_telegram_configuration(monkeypatch):
    monkeypatch.setenv("TOKEN", "telegram-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456789")

    config = Configuration()

    assert config.get_token() == "telegram-token"
    assert config.get_chat_id() == 123456789


def test_telegram_configuration_requires_chat_id(monkeypatch):
    monkeypatch.setenv("TOKEN", "telegram-token")
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    with pytest.raises(ValueError, match="TELEGRAM_CHAT_ID"):
        Configuration()
