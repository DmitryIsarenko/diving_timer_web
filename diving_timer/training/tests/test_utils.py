import pytest

from training.utils import format_duration


@pytest.mark.parametrize(
    ('total_seconds', 'expected_string'),
    (
        pytest.param(0, '00:00:00', id='Zero seconds'),
        pytest.param(1, '00:00:01', id='single-second'),
        pytest.param(59, '00:00:59', id='before-minute'),
        pytest.param(60, '00:01:00', id='exact-minute'),
        pytest.param(61, '00:01:01', id='minute-and-second'),
        pytest.param(3599, '00:59:59', id='before-hour'),
        pytest.param(3600, '01:00:00', id='exact-hour'),
        pytest.param(3661, '01:01:01', id='hour-minute-second'),
        pytest.param(86400, '24:00:00', id='exact-full-day'),
        pytest.param(360000, '100:00:00', id='three-digit-hours-100-hours'),
    ),
)
def test_format_duration(total_seconds: int, expected_string: str) -> None:
    """Format nonnegative durations as hours, minutes, and seconds."""
    assert format_duration(total_seconds) == expected_string


@pytest.mark.parametrize(
    ('total_seconds',),
    (
        pytest.param(-1, id='Minus 1 seconds'),
        pytest.param(-60, id='Minus 60 seconds'),
        pytest.param(-3600, id='Minus 3600 seconds'),
    ),
)
def test_format_duration_rejects_negative_seconds(total_seconds: int) -> None:
    """Formatting negative durations is not allowed."""
    with pytest.raises(ValueError):
        format_duration(total_seconds)
