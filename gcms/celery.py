"""
Celery configuration for GCMS project.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gcms.settings')

app = Celery('gcms')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    'send-daily-reports': {
        'task': 'analytics.tasks.generate_daily_report',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
    'send-weekly-reports': {
        'task': 'analytics.tasks.generate_weekly_report',
        'schedule': crontab(hour=2, minute=30, day_of_week=1),  # Monday 2:30 AM
    },
    'send-monthly-reports': {
        'task': 'analytics.tasks.generate_monthly_report',
        'schedule': crontab(hour=3, minute=0, day_of_month=1),  # 1st of month 3 AM
    },
    'backup-database': {
        'task': 'analytics.tasks.backup_database',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
    'archive-old-complaints': {
        'task': 'complaints.tasks.archive_old_complaints',
        'schedule': crontab(hour=3, minute=0),  # 3 AM daily
    },
    'verify-backup-integrity': {
        'task': 'analytics.tasks.verify_backup_integrity',
        'schedule': crontab(hour=4, minute=0, day_of_month=1),  # 1st of month 4 AM
    },
    'retrain-ai-models': {
        'task': 'ai_integration.tasks.retrain_categorization_model',
        'schedule': crontab(hour=1, minute=0, day_of_week=0),  # Sunday 1 AM
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
