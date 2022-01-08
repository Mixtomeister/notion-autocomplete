from celery import Celery

import os


app = Celery('notion', 
            broker=os.environ.get('CELERY_BROKER_URL'),
            backend=os.environ.get('CELERY_BACKEND_URL'),
            include=['checker.tasks', 'updater.tasks'])

app.conf.beat_schedule = {
    'check-every-second': {
        'task': 'checker.tasks.check',
        'schedule': 2.0,
        'args': ('be2a2e53a3b949cc9c83432063bf9ade',)
    },
}

app.conf.timezone = 'UTC'
