from Monitor import *
from Participant import *
from User import *
from Bot import *
# ---- 

import os

from dotenv import load_dotenv
load_dotenv()


api_key = os.getenv("CF_API_KEY")
api_secret = os.getenv("CF_API_SECRET")
telegram_token = os.getenv("TELEGRAM_TOKEN")

def main():
    bot = CodeforcesMonitorBot(
            token=telegram_token,
            api_key=api_key, 
            api_secret=api_secret
        )

    bot.run()

if __name__ == '__main__':
    
    main()
