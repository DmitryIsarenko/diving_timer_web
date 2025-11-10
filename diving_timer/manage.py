#!/usr/bin/env python
import os
import sys


def main() -> None:
    """Служит для запуска скрипта."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diving_timer.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError('Django is not installed or not available in the current environment.') from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
