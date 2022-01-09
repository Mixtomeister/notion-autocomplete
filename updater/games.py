from updater.base import BaseUpdater

from igdb.wrapper import IGDBWrapper
from igdb.igdbapi_pb2 import GameResult, GameCategoryEnum

from notion_client import Client as NotionClient

import os
import requests


def refresh_twitch_token():
    response = requests.post(
        url='https://id.twitch.tv/oauth2/token',
        params={
            'client_id': os.environ['IGDB_CLIENT_ID'],
            'client_secret': os.environ['IGDB_CLIENT_SECRET'],
            'grant_type': 'client_credentials'
        }
    )

    response.raise_for_status()

    response_body = response.json()

    os.environ['IGDB_API_TOKEN'] = response_body['access_token']


class GameUpdater(BaseUpdater):
    def __init__(self, page):
        super().__init__(page)

    def update(self):
        if 'IGDB_API_TOKEN' not in os.environ:
            refresh_twitch_token()

        name = self.page['properties']['Name']['title'][0]['plain_text'].strip()[2:-2]
        game = self._retrive(name)

        notion = NotionClient(auth=os.environ["NOTION_API_TOKEN"])

        notion.pages.update(
            **{
                "page_id": self.page['id'],
                "properties": {
                    "Name": {
                        "title": [
                            {
                                "type": "text",
                                "text": {
                                    "content": game['name']
                                }
                            }
                        ]
                    }
                }
            }
        )



    def _retrive(self, search):
        igdb = IGDBWrapper(os.environ.get('IGDB_CLIENT_ID'), os.environ.get('IGDB_API_TOKEN'))

        byte_array = igdb.api_request(
            'games.pb',
            f'fields name,category,first_release_date,franchise,genres,cover,involved_companies;search "{search}";'
        )

        response = GameResult()
        response.ParseFromString(byte_array)

        if not len(response.games):
            raise Exception('No games found')

        game = response.games[0]

        return {
            'name': self._get_name(game),
            'cover': self._get_cover(game.cover.image_id)
        }

    def _get_name(self, game):
        return game.name

    def _get_cover(self, image_id):
        return f'https://images.igdb.com/igdb/image/upload/t_cover_big/{image_id}.png'

