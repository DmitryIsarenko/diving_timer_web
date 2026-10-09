from pathlib import Path


def building_logging_config(
    *,
    base_dir: Path,
    debug: bool,
) -> dict[str, object]:
    """Build the Django logging configuration."""
    log_dir = base_dir / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)

    application_level = 'DEBUG' if debug else 'INFO'

    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'console': {
                'format': (
                    '[{levelname:<8}][{name}:{lineno}][msg: {message}]'
                ),
                'style': '{',
            },
            'file': {
                'format': (
                    '{asctime}|{levelname}|'
                    'module:{name}|'
                    'line:{lineno}|'
                    'function:{funcName}|'
                    'msg:{message}'
                ),
                'style': '{',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'DEBUG',
                'formatter': 'console',
                'stream': 'ext://sys.stdout',
            },
            'rotating_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'WARNING',
                'formatter': 'file',
                'filename': log_dir / 'diving_timer.log',
                'maxBytes': 1_000_000,
                'backupCount': 4,
                'encoding': 'utf-8',
                'delay': True,
            },
        },
        'loggers': {
            'accounts': {
                'handlers': ['console', 'rotating_file'],
                'level': application_level,
                'propagate': False,
            },
            'training': {
                'handlers': ['console', 'rotating_file'],
                'level': application_level,
                'propagate': False,
            },
            'diving_timer': {
                'handlers': ['console', 'rotating_file'],
                'level': application_level,
                'propagate': False,
            },
        },
    }
