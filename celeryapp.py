from celery import Celery


app = Celery('notion', 
            broker='pyamqp://guest@rabbit//', 
            backend='rpc://guest@rabbit//',
            include=['checker.tasks', 'updater.tasks'])

app.conf.beat_schedule = {
    'check-every-second': {
        'task': 'checker.tasks.check',
        'schedule': 1.0,
        'args': (1, 2, 3)
    },
}

app.conf.timezone = 'UTC'
