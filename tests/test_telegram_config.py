import pytest

from app.tg.config import Configuration, validate_telegram_configuration


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


def test_telegram_configuration_requires_token(monkeypatch):
    monkeypatch.delenv("TOKEN", raising=False)
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456789")

    with pytest.raises(ValueError, match="TOKEN"):
        validate_telegram_configuration()


def test_telegram_configuration_rejects_non_numeric_chat_id(monkeypatch):
    monkeypatch.setenv("TOKEN", "telegram-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "not-a-chat-id")

    with pytest.raises(ValueError, match="must be an integer"):
        validate_telegram_configuration()
