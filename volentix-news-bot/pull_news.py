import json
import traceback
from urllib.request import urlopen, Request

import asyncio

import discord
from bs4 import BeautifulSoup
from pymongo import MongoClient

with open('../services.json') as conf_file:
    conf = json.load(conf_file)
    connectionString = conf['volentix_mongo']['connectionString']
    discord_bot_token = conf['discord']['reveal_token']
    news_channel = conf['discord']['news_channel_id']

db_client = MongoClient(connectionString)
db = db_client.get_default_database()
col_articles = db['news']


class VTXNews:


    def __init__(self, dc_client):
        self.client = dc_client


    async def get_content_voloro(self):
        try:
            result = Request('https://valoro.io/library/',
                             headers={'User-Agent': 'Mozilla/5.0'})
            result = urlopen(result).read()

            soup = BeautifulSoup(result, 'lxml')

            attrs = list(soup.find_all(class_="library-blog"))
            article = col_articles.find_one({"_id": "voloro"})

            for x in attrs:
                data_id_last = str(attrs[0].contents[1].attrs['href'])
                data_id = str(x.contents[1].attrs['href'])
                if article is not None:
                    article_num = article['article_num']
                    if article_num != data_id:
                        title = x.contents[3].text
                        body = x.contents[5].text
                        col_articles.update(
                            {
                                "_id": "voloro"
                            },
                            {
                                "$set":
                                    {
                                        "article_num": data_id_last
                                    }
                            },
                            upsert=True
                        )
                        msg = "**%s**\n%s\n%s" % (title, body, data_id)
                        await self.client.send_message(client.get_channel(news_channel), msg)
                        break
                    else:
                        break

                else:
                    col_articles.update(
                        {
                            "_id": "voloro"
                        },
                        {
                            "$set":
                                {
                                    "article_num": str(attrs[4].contents[1].attrs['href'])
                                }
                        },
                        upsert=True
                    )
                    break
        except Exception as exc:
            print(exc)
            print(str(traceback.print_exc()))



client = discord.Client()
news_obj = VTXNews(client)


"""
    Handle event when bot is ready to use
"""
@client.event
async def on_ready():
    print('Logged in as:')
    print(client.user.name)
    print(client.user.id)
    print('------')
    await news_obj.get_content_voloro()
    await asyncio.sleep(1)
    # Logout
    await client.logout()
    # Bot disconnect
    await client.close()

client.run(discord_bot_token)
