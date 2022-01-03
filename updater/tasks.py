from celeryapp import app

@app.task(queue='updater')
def update(database_id, client_id, client_secret, item, item_data):
    return 'UPDATE!!!'