from celeryapp import app
from updater.tasks import update_page_task
from notion_client import Client

import os


@app.task(queue='checker')
def check_task(database_id):
    notion = Client(auth=os.environ["NOTION_API_TOKEN"])
    
    query = notion.databases.query(
        **{
            "database_id": database_id,
            "filter": {
                "and": [
                    {
                        "property": "Name",
                        "text": {
                            "starts_with": "{{"
                        }
                    },
                    {
                        "property": "Name",
                        "text": {
                            "ends_with": "}}"
                        }
                    }
                ]
            }
        }
    )

    if 'results' in query and query['results']:
        for page in query['results']:
            update_page_task.delay(page)
