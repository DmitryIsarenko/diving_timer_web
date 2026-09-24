def format_duration(total_seconds: int) -> str:
    """Formats seconds into user-friendly UI."""
    if total_seconds < 0:
        raise ValueError('Duration cannot be negative.')
    hours, remaining_seconds = divmod(total_seconds, 3600)
    minutes, remaining_seconds = divmod(remaining_seconds, 60)

    return f'{hours:02d}:{minutes:02d}:{remaining_seconds:02d}'
