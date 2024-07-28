import requests
import json
from telegram import Bot
import asyncio
from datetime import datetime, timedelta
import telebot

# Set all variables at the top
CMC_API_KEY = "5c0c6dea-e42d-4fef-83f3-07edcdc832e1"
CMC_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
TELEGRAM_BOT_TOKEN = "5953937447:AAH1KCsL6BO3pc2DndLPMcl7S18gAS3b6Xw"

# Function to get cryptocurrency data
def get_crypto_data(crypto):
    try:
        headers = {'X-CMC_PRO_API_KEY': CMC_API_KEY}
        parameters = {'symbol': crypto}
        
        response = requests.get(CMC_URL, headers=headers, params=parameters)
        data = response.json()
        
        if response.status_code == 200:
            crypto_name = data['data'][crypto]['name']
            crypto_price = data['data'][crypto]['quote']['USD']['price']
            crypto_percent_change_24h = data['data'][crypto]['quote']['USD']['percent_change_24h']
            crypto_volume_24h = data['data'][crypto]['quote']['USD']['volume_24h']

            return crypto_name, crypto_price, crypto_percent_change_24h, crypto_volume_24h
        else:
            response.raise_for_status()
    except Exception as e:
        print(f"Error occurred while fetching data for {crypto}: {e}")
        return None, None, None, None

# Function to send a message to Telegram
async def send_message(crypto_name, crypto_price, crypto_percent_change_24h, crypto_volume_24h, bot_token, chat_id):
    try:
        message = f'{crypto_name}\nPrice: ${crypto_price}\nChange: {crypto_percent_change_24h}%\nVolume: ${crypto_volume_24h}'
        bot = Bot(token=bot_token)
        await bot.send_message(chat_id=chat_id, text=message)
    except Exception as e:
        print(f"Error occurred while sending message for {crypto_name}: {e}")

# Function to track cryptocurrency data and send messages periodically
async def track_crypto(crypto_list, bot_token, chat_id, time_interval, total_duration):
    start_time = datetime.now()
    end_time = start_time + timedelta(seconds=total_duration)
    
    while datetime.now() < end_time:
        for crypto in crypto_list:
            crypto_name, crypto_price, crypto_percent_change_24h, crypto_volume_24h = get_crypto_data(crypto)
            if crypto_name is not None:
                await send_message(crypto_name, crypto_price, crypto_percent_change_24h, crypto_volume_24h, bot_token, chat_id)
        await asyncio.sleep(time_interval)

# Function to start tracking
def start_tracking(symbols, time_interval, chat_id, total_duration):
    asyncio.run(track_crypto(symbols, TELEGRAM_BOT_TOKEN, chat_id, time_interval, total_duration))

# Initialize Telegram bot
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
user_data = {}

# Command to start interaction with the bot
@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        user_data[chat_id] = {}
        
    if 'crypto_symbols' not in user_data[chat_id]:
        bot.send_message(chat_id, "Welcome to the cryptocurrency tracking bot! Which cryptocurrencies would you like to track like btc, eth, sol, ada, etc.? (Enter symbols separated by commas)")
        return
    
    if 'time_interval' not in user_data[chat_id]:
        crypto_symbols = user_data[chat_id]['crypto_symbols']
        bot.send_message(chat_id, f"Please enter the time interval (in seconds) for tracking {', '.join(crypto_symbols)}:")
        return
    
    if 'total_duration' not in user_data[chat_id]:
        bot.send_message(chat_id, "Please enter the total duration (in seconds) for tracking:")

# Handler to get cryptocurrency symbols
@bot.message_handler(func=lambda message: message.chat.id in user_data 
                                          and 'crypto_symbols' not in user_data[message.chat.id])
def get_crypto_symbols(message):
    chat_id = message.chat.id
    crypto_symbols = message.text.upper().split(',')
    crypto_symbols = [symbol.strip() for symbol in crypto_symbols]
    
    user_data[chat_id]['crypto_symbols'] = crypto_symbols
    
    bot.send_message(chat_id, "Please enter the time interval (in seconds) for tracking:")

# Handler to get time interval
@bot.message_handler(func=lambda message: message.chat.id in user_data 
                                          and 'crypto_symbols' in user_data[message.chat.id]
                                          and 'time_interval' not in user_data[message.chat.id])
def get_time_interval(message):
    chat_id = message.chat.id
    time_interval = int(message.text)
    crypto_symbols = user_data[chat_id]['crypto_symbols']
    user_data[chat_id]['time_interval'] = time_interval
    bot.send_message(chat_id, f"Please enter the total duration (in seconds) for tracking:")

# Handler to get total duration
@bot.message_handler(func=lambda message: message.chat.id in user_data 
                                          and 'crypto_symbols' in user_data[message.chat.id]
                                          and 'time_interval' in user_data[message.chat.id]
                                          and 'total_duration' not in user_data[message.chat.id])
def get_total_duration(message):
    chat_id = message.chat.id
    total_duration = int(message.text)
    crypto_symbols = user_data[chat_id]['crypto_symbols']
    time_interval = user_data[chat_id]['time_interval']
    user_data[chat_id]['total_duration'] = total_duration
    bot.send_message(chat_id, f"Tracking {', '.join(crypto_symbols)} every {time_interval} seconds for a total duration of {total_duration} seconds...")
    start_tracking(crypto_symbols, time_interval, chat_id, total_duration)

# Start bot polling
bot.polling()
