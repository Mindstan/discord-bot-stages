# discord-bot-stages

Bot Discord pour les stages

## Requirements

### To run the bot

* Python 3.5 or higher
* python-dotenv
* discord.py
* aiohttp
* pytz

The Python modules can be installed with `pip install python-dotenv discord.py aiohttp pytz` if you have pip installed.

### To run the API

* Docker

## Configuration

### Bot

The bot needs a bot token from Discord. Once obtained, create a `.env` file containing the following line :
```
API_URL=[URL to progress-tracker (ex : http://website.com)]
API_TOKEN=TOKEN [token for progress-tracker]
DISCORD_TOKEN=[your token]
```

Please refer to the Discord documentation on how to create a bot token and invite it to your server.


### API

Create a file `env-vars` containing :
```
API_TOKEN=TOKEN [token for the API]
DJANGO_SECRET_KEY=[Django secret key]
INDEX_USERPASS=[username for the index page]:[password for the index page]
```
