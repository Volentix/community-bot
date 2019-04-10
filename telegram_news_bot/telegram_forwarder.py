import json
import traceback

import asyncio
import discord
from telegram import Bot
from telethon import TelegramClient, sync
from telethon.tl.functions.channels import GetFullChannelRequest
from pymongo import MongoClient


"""
    Get parametrs from the config
"""
with open("../services.json") as file:
    conf = json.load(file)
    connectionString = conf['volentix_mongo']['connectionString']
    discord_bot_token = conf['discord']['reveal_token']
    telegram_bot_token = conf['telegram']['bot_token']
    news_channel_id = conf['discord']['announcements_channel_id']
    tg_news_channel = conf['telegram']['news_channel']
    chats = conf['telegram']['chats']


client = discord.Client()


class TgAnnouncements:
    def __init__(self, client):

        self.client = client

        # Mongodb initialization
        mongo_client = MongoClient(connectionString)
        db = mongo_client.get_default_database()
        self.tg_collection = db['tg_news']

        self.tg_bot = Bot(telegram_bot_token)
        # init tg user
        self.telegram_client = None


    """
        User Authentication required phone number with the code
    """
    def telegram_auth(self):
        try:
            telegram_client = TelegramClient(
                'volentix_session',
                api_id=API_ID,
                api_hash=API_HASH).start()
            print("SUCCESS")
            return telegram_client

        except Exception as e:
            print(e)
            print(traceback.print_exc())

    """
        Disconnect Telegram Client
    """
    def disconnect(self):
        self.telegram_client.disconnect()


    """
        Check last telegram news channel posts 
    """
    def check_last_news(self):
        try:
            channel_entity = self.telegram_client(GetFullChannelRequest(tg_news_channel)).chats[0]
            return self.message_processing(channel_entity)

        except Exception as exc:
            print(exc)
            traceback.print_exc()


    """
        Send telegram smg
    """
    def tg_send_message(self, msg):
        for _chat in chats:
            try:
                self.tg_bot.send_message(
                    _chat,
                    msg
                )

            except Exception as exc:
                print(exc)



    """
        Processing each new msg from the telegram channel and send it to the discord channel
    """
    def message_processing(self, entity):
        msgs = []
        db_item = self.tg_collection.find_one({"_id": entity.username})

        if db_item is not None:
            try:
                messages = self.telegram_client.get_messages(entity, 10, min_id=int(db_item['MsgId']))
                self.tg_collection.update(
                    {
                        "_id": entity.username
                    },
                    {
                        "_id": entity.username,
                        "MsgId": messages[0].id
                    }, upsert=True
                )

                for _msg in messages:
                    try:
                        msgs.append(_msg.text)
                    except Exception as exc:
                        print(exc)
                        traceback.print_exc()
                return msgs
            except Exception as exc:
                print(exc)
                return msgs

        else:
            messages = self.telegram_client.get_messages(entity, 10)
            self.tg_collection.update(
                {
                    "_id": entity.username
                },
                {
                    "_id": entity.username,
                    "MsgId": messages[1].id
                }, upsert=True
            )
            return msgs


obj = TgAnnouncements(client)
obj.telegram_client = obj.telegram_auth()
msgs = obj.check_last_news()
obj.disconnect()


"""
    Send news to discord channel
"""
async def send_news_to_channel(text):
    await client.wait_until_ready()
    await client.send_message(client.get_channel(news_channel_id), text)


"""
    Handle event when bot is ready to use
"""
@client.event
async def on_ready():
    print('Logged in as:')
    print(client.user.name)
    print(client.user.id)
    print('------')

    for _msg in msgs:
        try:
            print(_msg, len(_msg))
            await send_news_to_channel(_msg)
            obj.tg_send_message(_msg)
        except Exception as exc:
            print(exc)
    asyncio.sleep(5)
    # Logout
    await client.logout()
    # Bot disconnect
    await client.close()


if len(msgs) > 0:
    client.run(discord_bot_token)