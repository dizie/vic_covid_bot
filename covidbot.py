from requests_oauthlib import OAuth1Session
from discord_bot import bot
from os import path
import json
import objectpath
import requests
import shutil
import logging

config = {}
logger_conf = {}

last_id = None

logger = None


def check_for_conf():
    no_conf = False
    if not path.exists('config.json'):
        shutil.copyfile('config.json.example', 'config.json')
        no_conf = True
    if not path.exists('discord.json'):
        shutil.copyfile('discord.json.example', 'discord.json')
        no_conf = True

    if no_conf is True:
        if logger is not None and logger_conf['console_logger'] is not False:
            logger.error("Config file(s) missing, please check config files and try again.")
        elif logger is not None:
            logger.error("Config file(s) missing, please check config files and try again.")
            print("Config file(s) missing, please check config files and try again.")
        else:
            print("Config file(s) missing,please check config files and try again.")
        exit(1)


def get_logger():
    with open('logging.json', 'r') as l:
        global logger_conf
        logger_conf = json.load(l)

    logging.basicConfig(format=logger_conf['log_format'],
                        datefmt=logger_conf['date_format'],
                        filename=logger_conf['log_path'],
                        level=logging.INFO)

    if logger_conf['console_logger'] is True:
        console = logging.StreamHandler()
        console.setLevel(logging.getLevelName(logger_conf['console_log_level']))
        console.setFormatter(logging.Formatter(logger_conf['log_format']))
        logging.getLogger('').addHandler(console)

    global logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.getLevelName(logger_conf['log_level']))


def process_last(ident=None):
    if ident is None:
        global last_id
        try:
            with open('last.txt', 'r') as f:
                last_id = int(f.read())
        except FileNotFoundError:
            last_id = 1
    else:
        with open('last.txt', 'w') as f:
            f.write(str(ident))


def load_config(config_file="config.json"):
    if path.exists('logging.json'):
        get_logger()
    check_for_conf()
    with open(config_file, 'r') as f:
        global config
        config = json.load(f)

    process_last()


def build_query():
    base_url = config['twitter_base_url'] + config['twitter_api_version'] + config['twitter_api_uri']
    query_url = config['twitter_search_args'].format(config['search_user'], config['search_show_retweets'],
                                                     config['search_hide_replies'], last_id)
    return base_url + query_url


def get_payload():
    outh = OAuth1Session(config['twitter_consumer_key'],
                         client_secret=config['twitter_consumer_secret'],
                         resource_owner_key=config['twitter_access_token'],
                         resource_owner_secret=config['twitter_access_secret'])

    params = {}

    return outh.get(build_query(), params=params).json()


def parse_payload():
    for e in get_payload():
        op = objectpath.Tree(e)
        hashtags = str(op.execute('$.entities.hashtags'))
        full_body = str(op.execute('$.full_text')).replace("&amp;", "&")
        if any(hashtag in hashtags for hashtag in config['hashtag_search']) \
                and config['body_filter'] in full_body \
                and config['body_exclude'] not in full_body:
            return op.execute('$.id'), full_body, op.execute('$.entities.media[0].media_url')


def download_image(url, ident):
    req = requests.get(url, stream=True)
    req.raw.decode_content = True

    filename = str(ident) + ".jpg"
    with open(filename, 'wb') as img:
        shutil.copyfileobj(req.raw, img)

    return filename


def main():
    load_config()
    try:
        tweet_id, tweet_body, tweet_image = parse_payload()
        if logger is not None:
            logger.info("id = {} \ntext = {} \nmedia = {}".format(tweet_id, tweet_body, tweet_image))
        bot(tweet_body, 'discord.json', download_image(tweet_image, tweet_id))
        process_last(tweet_id)
    except TypeError:
        if logger is not None:
            logger.info("No new tweets found")


if __name__ == "__main__":
    main()
