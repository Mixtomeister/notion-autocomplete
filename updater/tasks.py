from celeryapp import app

from updater.games import GameUpdater, refresh_twitch_token


@app.task(queue='updater')
def twitch_auth_task():
    refresh_twitch_token()


@app.task(queue='updater')
def update_page_task(page):
    updater = GameUpdater(page)

    updater.update()
