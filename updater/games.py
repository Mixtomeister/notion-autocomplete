from updater.base import BaseUpdater

from igdb.wrapper import IGDBWrapper
from igdb.igdbapi_pb2 import GameResult, GameCategoryEnum

from notion_client import Client as NotionClient

from datetime import datetime

import os
import requests
import re


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

        properties = {}
        cover = None

        if 'name' in game and game['name']:
            properties['Name'] = { "title": game['name'] }

        if 'collection' in game and game['collection']:
            properties['Collection'] = { "select": game['collection'] }

        if 'category' in game and game['category']:
            properties['Type'] = { "select": game['category'] }

        if 'developers' in game and game['developers']:
            properties['Developers'] = { "multi_select": game['developers'] }

        if 'publishers' in game and game['publishers']:
            properties['Publishers'] = { "multi_select": game['publishers'] }
        
        if 'Publishers' not in properties and 'Developers' in properties:
            properties['Publishers'] = properties['Developers']

        if 'genres' in game and game['genres']:
            properties['Genres'] = { "multi_select": game['genres'] }

        if 'release_date' in game and game['release_date']:
            properties['Release date'] = { "date": game['release_date'] }

        if 'cover' in game and game['cover']:
            cover = {
                "type": "external",
                "external": {
                    "url": game['cover']
                }
            }

        notion.pages.update(
            **{
                "page_id": self.page['id'],
                "properties": properties,
                'cover': cover
            }
        )



    def _retrieve(self, search):
        igdb = IGDBWrapper(os.environ.get('IGDB_CLIENT_ID'), os.environ.get('IGDB_API_TOKEN'))
        query = f'search "{search}"'

        if re.match('igdb:[1-9]+', search):
            igdb_id = int(search.split(':')[1])
            query = f'where id = {igdb_id}'

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
            {query};
            '''
        )

        response = GameResult()
        response.ParseFromString(byte_array)

        if not len(response.games):
            return {
                'name': self._get_name('Game not found')
            }


        game = response.games[0]

        return {
            'name': self._get_name(game.name),
            'cover': self._get_cover(game.cover.image_id),
            'collection': self._get_collection(game.collection.name),
            'release_date': self._get_release_date(game.first_release_date.seconds),
            'developers': self._get_developers(game.involved_companies),
            'publishers': self._get_publishers(game.involved_companies),
            'genres': self._get_genres(game.genres),
            'category': self._get_category(game.category)
        }

    def _get_name(self, name):
        if name:
            return [
                {
                    "type": "text",
                    "text": {
                        "content": self._remove_commas(name)
                    }
                }
            ]

    def _get_cover(self, image_id):
        if image_id:
            return f'https://images.igdb.com/igdb/image/upload/t_cover_big/{image_id}.png'

    def _get_collection(self, name):
        if name:
            return {'name': self._remove_commas(name)}

    def _get_release_date(self, timestamp):
        return {'start': datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d')}

    def _get_developers(self, involved_companies):
        developers = []

        for i in involved_companies:
            if i.developer or i.porting:
                developers.append({'name': self._remove_commas(i.company.name)})
        
        if developers:
            return developers

    def _get_publishers(self, involved_companies):
        publishers = []

        for i in involved_companies:
            if i.publisher:
                publishers.append({'name': self._remove_commas(i.company.name)})

        if publishers:
            return publishers

    def _get_genres(self, genres):
        if genres:
            return [{'name': self._remove_commas(i.name)} for i in genres]

    def _get_category(self, category):
        return {'name': self._remove_commas(GameCategoryEnum.Name(category).replace('_', ' ').capitalize())}

    def _remove_commas(self, text):
        return text.replace(',', '')
