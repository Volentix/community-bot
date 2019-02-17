import json
import string
from random import randint, random, choice
import datetime
import discord
from pymongo import MongoClient

with open('../services.json') as file:
    config = json.load(file)
    discord_bot_token = config['discord']['reveal_token']
    welcome_msgs_list = config['discord']['welcome_list']
    connectionString = config['volentix_mongo']['connectionString']
    welcome_channel = config['discord']['welcome_channel_id']

client = discord.Client()

# Mongo init
mongo_client = MongoClient(connectionString)
db = mongo_client.get_default_database()
users_col = db['Users']


WELCOME_MSG = """
🔰 Official website : https://VOLENTIX.io
🔰 Twitter : https://twitter.com/VOLENTIX
🔰 News and Videos : https://www.valoro.io 
🔰 Facebook : https://facebook.com/VOLENTIX
🔰 Telegram: http://t.me/VOLENTIX
"""


"""
    Handle event when user joined, notify.
"""
@client.event
async def on_member_join(member):
    e = discord.Embed(color=0x7289da)
    e.add_field(name='**Welcome to Volentix Discord Community**', value=WELCOME_MSG,
                inline=True)
    await client.send_message(member, """**What is Volentix?**\n\nVolentix is a Digital Assets Ecosystem (DAE) combining a Decentralized digital assets Exchange (VDEX) with a secure multi-currency cross-blockchain peer-to-peer wallet, (VERTO) a user-friendly market-ratings analytical interface powered by AI, (VESPUCCI) and an incentives-based recruitment program (VENUE) """)
    await client.send_message(member, embed=e)
    await client.send_message(client.get_channel(welcome_channel),
                              welcome_msgs_list[randint(0, len(welcome_msgs_list)-1)].format(member))
    captcha = register_account(member)
    if captcha is not None:
        e = discord.Embed(color=0x7289da)
        e.add_field(name='**Write below to send messages**',
                    value=captcha,
                    inline=True)
        await client.send_message(member, "Write below Number: **%s** to send messages in Volentix Server" % captcha)


def register_account(member):
    account = users_col.find_one({'DiscordAccountId': member.id})
    if account is None:
        steem_memo = generate_memo()
        telegram_memo = generate_telegram_memo()
        captcha = str(randint(0, 3000))

        users_col.update(
            {
                "DiscordAccountId": member.id
            },
            {
                "$set":
                    {
                        "DiscordAccountId": member.id,
                        "DiscordMemo": captcha,
                        "DiscordName": None,
                        "SteemUserName": None,
                        "SteemMemo": steem_memo,
                        "TelegramMemo": telegram_memo,
                        "TelegramUserId": None,
                        "VTXAddress": None,
                        'CreatedAt': datetime.datetime.now(),
                        "TokenBalance": 0,
                        "LastAction": "Verification",
                    }
            }, upsert=True
        )
        return captcha
    else:
        return None


"""
    Generate memo to link account
"""
def generate_memo():
    difficulty = 3
    symbols_count = 9
    memo = '-'.join(''.join(
        choice(string.ascii_uppercase + string.digits) for _ in
        range(symbols_count)) for _ in range(difficulty))
    return memo


"""
    Generate telegram memo
"""
def generate_telegram_memo():
    symbols_count = 9
    memo = ''.join(
        choice(string.ascii_uppercase + string.digits) for _ in
        range(symbols_count))
    return memo

"""
    Get specified discord channel
"""
def get_discord_channel(channel):
    channels = client.get_all_channels()
    for _channel in channels:
        if _channel.name == channel:
            return _channel
    return None


@client.event
async def on_message(message):
    try:
        if message.author == client.user:
            return
        account = users_col.find_one({'DiscordAccountId': message.author.id})
        if account is not None:
            last_action = account['LastAction']
            captcha = account['DiscordMemo']
            if last_action == 'Verification' and \
                    str(captcha) == str(message.content):
                await client.send_message(message.author,
                                          "Thank you! Now you can send messages in Volentix Server!")
                server = client.get_server('521016144979820544')
                role = discord.utils.get(server.roles, name="Priviledge")
                await client.add_roles(server.get_member(message.author.id), role)
                users_col.update(
                    {
                        "DiscordAccountId": message.author.id
                    },
                    {
                        "$set":
                            {
                                "DiscordName": str(message.author),
                                "LastAction": None,
                            }
                    }, upsert=True
                )

            elif last_action == 'Verification':
                await client.send_message(message.author,
                                          "You written incorrect number!")

        if message.content.startswith('!welcome'):
            await on_member_join(message.author)
    except Exception as exc:
        print(exc)


@client.event
async def on_ready():
    print('Logged in as:')
    print(client.user.name)
    print(client.user.id)
    print('------')



client.run(discord_bot_token)
