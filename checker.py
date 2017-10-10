import time
from getpass import getpass
from steam_worker import SteamWorker
from telegram.ext import Updater
from secrets import telegram_token, telegram_chat_id, steam_username
import telegram
import logging

# Set up logging for server events
logging.basicConfig(format="%(asctime)s | %(name)s | %(message)s",
                    level=logging.INFO)

LOG = logging.getLogger('SimpleWebAPI')

# Set up connection to Telegram room and dispatch, for sending messages
# Grab the user token for the telegram room from secrets.py
updater = Updater(token=telegram_token)
dispatcher = updater.dispatcher

# Set up Telegram bot
bot = telegram.Bot(token=telegram_token)


def alertChat(bot, message):
    """Send a message to the the chat"""
    # Grab the ID for the Telegram room from secrets.py
    bot.sendMessage(chat_id=telegram_chat_id, text=message)


# Initialize the worker
worker = SteamWorker()

# Attempt to start the worker, and catch any event that may come from
# a failed creation call
try:
    # Grab the steam username from secrets.py
    worker.start(username=steam_username, password=getpass())
except:
    raise SystemExit

# Set the changenumber to 0 so that we always get a new change number when
# starting the service
changenumber = 0


while True:
    """
    Check every second for a new change number.
    If the server returns nothing, alert the chat and
    send no messages for 60 seconds.
    If there is a new change number, alert the chat accordingly.
    """
    try:
        LOG.info("Checking for new changenumber")

        # Hit the API for a new changenumber
        resp = worker.get_change_number(570)

        # If the server returns nothing, cooldown for 60 seconds
        if resp == '{}' and changenumber != 0:
            LOG.info("No response from server, cooling down")
            msg = "The Dota2 API failed to respond, cooling down."
            alertChat(bot, msg)
            time.sleep(60)
            continue

        # If there is a new changenumber, save it and alert the chat
        if resp != changenumber:
            LOG.info("New changenumber detected")
            changenumber = resp
            msg = "New ChangeNumber for Dota2: " + str(resp)
            alertChat(bot, msg)
            LOG.info(msg)
        time.sleep(1)

    # If the user ctrl-c's out, log out of the user account
    except KeyboardInterrupt:
        LOG.info("Exit requested")
        worker.close()
        break

# Log out of the user account
worker.close()
