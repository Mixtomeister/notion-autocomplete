from updater.base import BaseUpdater

from igdb.wrapper import IGDBWrapper
from igdb.igdbapi_pb2 import GameResult, GameCategoryEnum

from notion_client import Client as NotionClient

from datetime import datetime

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
        game = self._retrieve(name)

        notion = NotionClient(auth=os.environ["NOTION_API_TOKEN"])

        notion.pages.update(
            **{
                "page_id": self.page['id'],
                "properties": {
                    "Name": {
                        "title": game['name']
                    },
                    'Collection': {
                        'select': game['collection']
                    },
                    'Type': {
                        'select': game['category']
                    },
                    'Developers': {
                        'multi_select': game['developers']
                    },
                    'Publishers': {
                        'multi_select': game['publishers']
                    },
                    'Genres': {
                        'multi_select': game['genres']
                    },
                    'Release date': {
                        'date': game['release_date']
                    }
                },
                'cover': {
                    "type": "external",
                    "external": {
                        "url": game['cover']
                    }
                }
            }
        )



    def _retrieve(self, search):
        igdb = IGDBWrapper(os.environ.get('IGDB_CLIENT_ID'), os.environ.get('IGDB_API_TOKEN'))

        byte_array = igdb.api_request(
            'games.pb',
            f'''
            fields 
            name,
            category,
            first_release_date,
            collection.name,
            genres.name,
            cover.image_id,
            involved_companies.company.name,
            involved_companies.developer,
            involved_companies.porting,
            involved_companies.publisher;
            search "{search}";
            '''
        )

        response = GameResult()
        response.ParseFromString(byte_array)

        if not len(response.games):
            raise Exception('No games found')

        game = response.games[0]

        return {
            'name': self._get_name(game),
            'cover': self._get_cover(game),
            'collection': self._get_collection(game),
            'release_date': self._get_release_date(game),
            'developers': self._get_developers(game),
            'publishers': self._get_publishers(game),
            'genres': self._get_genres(game),
            'category': self._get_category(game)
        }

    def _get_name(self, game):
        return [
            {
                "type": "text",
                "text": {
                    "content": game.name
                }
            }
        ]

    def _get_cover(self, game):
        return f'https://images.igdb.com/igdb/image/upload/t_cover_big/{game.cover.image_id}.png'

    def _get_collection(self, game):
        return {'name': game.collection.name}

    def _get_release_date(self, game):
        return {'start': datetime.utcfromtimestamp(game.first_release_date.seconds).strftime('%Y-%m-%d')}

    def _get_developers(self, game):
        developers = []

        for i in game.involved_companies:
            if i.developer or i.porting:
                developers.append({'name': i.company.name})

        return developers

    def _get_publishers(self, game):
        publishers = []

        for i in game.involved_companies:
            if i.publisher:
                publishers.append({'name': i.company.name})

        return publishers

    def _get_genres(self, game):
        return [{'name': i.name} for i in game.genres]

    def _get_category(self, game):
        return {'name': GameCategoryEnum.Name(game.category).replace('_', ' ').capitalize()}
