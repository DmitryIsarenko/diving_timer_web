import os

from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diving_timer.settings')
app = Celery('diving_timer')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self) -> None:  # noqa: ANN001
    """Debug celery task."""
    print(f'Request: {self.request!r}')
