from celery import Celery
from celery.schedules import crontab

import os


app = Celery('notion', 
            broker=os.environ.get('CELERY_BROKER_URL'),
            backend=os.environ.get('CELERY_BACKEND_URL'),
            include=['checker.tasks', 'updater.tasks'])

app.conf.beat_schedule = {
    'check-games-every-second': {
        'task': 'checker.tasks.check_task',
        'schedule': 3.0,
        'args': ('be2a2e53a3b949cc9c83432063bf9ade',)
    },
    'twitch-auth': {
        'task': 'updater.tasks.twitch_auth_task',
        'schedule': 1.0 * 60 * 60,
    }
}

app.conf.timezone = 'UTC'
