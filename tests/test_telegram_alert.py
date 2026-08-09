import logging

from app.tg.alert import _handle_send_result


class FailedTask:
    def result(self):
        raise RuntimeError("https://api.telegram.org/botSECRET-TOKEN/sendMessage")


def test_delivery_failure_does_not_log_exception_details(caplog):
    with caplog.at_level(logging.ERROR, logger="app.tg.alert"):
        _handle_send_result(FailedTask())

    messages = "\n".join(record.getMessage() for record in caplog.records)
    assert "Telegram message delivery failed (RuntimeError)" in messages
    assert "SECRET-TOKEN" not in messages
