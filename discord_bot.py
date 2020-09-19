import json
import asyncio
import discord

config = {}


def load_config(config_file):
    with open(config_file, 'r') as f:
        global config
        config = json.load(f)


async def send_message(content, attachment=None):
    client = discord.Client()
    message = content

    @client.event
    async def on_ready():
        if attachment is None:
            await client.get_channel(config['channel_id']).send(message)
        else:
            await client.get_channel(config['channel_id']).send(message, file=discord.File(attachment))
        await client.close()

    await client.login(config['token'], bot=True)
    await client.connect()


def bot(message, config_file="conf.json",  attachment=None):
    load_config(config_file)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(send_message(message, attachment))


if __name__ == "__main__":
    bot("This is a test")
