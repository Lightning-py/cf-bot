from Monitor import *
from Participant import *
from User import *
from Bot import *
# ---- 

import os



api_key = os.getenv("CF_API_KEY")
api_secret = os.getenv("CF_API_SECRET")
telegram_token = os.getenv("TELEGRAM_TOKEN")


if __name__ == '__main__':
    
    bot = CodeforcesMonitorBot(
        token=telegram_token,
        api_key=api_key,
        api_secret=api_secret
    )
    bot.run()