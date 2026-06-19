from app.job_runner import retry_delay_seconds


def test_retry_delay_uses_exponential_backoff() -> None:
    assert retry_delay_seconds(1) == 30
    assert retry_delay_seconds(2) == 120
    assert retry_delay_seconds(3) == 480
