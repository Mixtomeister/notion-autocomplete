from celeryapp import app

@app.task(queue='checker')
def check(database_id, client_id, client_secret):
    return 'CHECKED!!!'