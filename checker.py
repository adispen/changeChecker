import json
import time
from getpass import getpass
from steam_worker import SteamWorker
from telegram.ext import Updater
from secrets import telegram_token, telegram_chat_id, steam_username
import telegram
import logging

logging.basicConfig(format="%(asctime)s | %(name)s | %(message)s", level=logging.INFO)
LOG = logging.getLogger('SimpleWebAPI')

updater = Updater(token=telegram_token)
dispatcher = updater.dispatcher

bot = telegram.Bot(token=telegram_token)

def alertChat(bot, message):
    bot.sendMessage(chat_id=telegram_chat_id, text=message)

worker = SteamWorker()

try:
    worker.start(username=steam_username, password=getpass())
except:
    raise SystemExit

changenumber = 0
while True:
    try:
        LOG.info("Checking for new changenumber")
        resp = worker.get_change_number(570)
        if resp != changenumber:
            LOG.info("New changenumber detected")
            changenumber = resp         
            msg = "New ChangeNumber for Dota2: " + str(resp)
            alertChat(bot, msg)
            LOG.info(msg)
        time.sleep(1)
    except KeyboardInterrupt:
        LOG.info("Exit requested")
        worker.close()
        break

worker.close()
