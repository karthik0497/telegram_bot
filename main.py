import logging,os
import requests
import asyncio
from datetime import datetime, timedelta
from telebot import TeleBot  # Ensure you're using the correct import

bot_token="5953937447:AAH1KCsL6BO3pc2DndLPMcl7S18gAS3b6Xw"
bot = TeleBot(bot_token)  # Initialize the TeleBot object

url="https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
# Setup logging
logging.basicConfig(filename='bot_log.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

user_data = {}

def log_interaction(message):
    user_id = message.from_user.id
    user_input = message.text
    user_status = user_data.get(user_id, {})
    logging.info(f'User ID: {user_id} - Input: {user_input} - Status: {user_status}')

def get_crypto_data(crypto):
    try:
        headers = {'X-CMC_PRO_API_KEY': "5c0c6dea-e42d-4fef-83f3-07edcdc832e1"}
        parameters = {'symbol': crypto}

        response = requests.get(url, headers=headers, params=parameters)
        data = response.json()

        if response.status_code == 200:
            crypto_info = data['data'][crypto]['quote']['USD']
            return data['data'][crypto]['name'], crypto_info['price'], crypto_info['percent_change_24h'], crypto_info['volume_24h']
        else:
            response.raise_for_status()
    except Exception as e:
        error_msg = f"Error occurred while fetching data for {crypto}: {e}"
        logging.error(error_msg)
        print(error_msg)
        return None, None, None, None

async def send_message(crypto_name, crypto_price, crypto_percent_change_24h, crypto_volume_24h, chat_id):
    try:
        message = f'{crypto_name}\nPrice: ${crypto_price}\nChange: {crypto_percent_change_24h}%\nVolume: ${crypto_volume_24h}'
        await bot.send_message(chat_id=chat_id, text=message)
    except Exception as e:
        error_msg = f"Error occurred while sending message for {crypto_name}: {e}"
        logging.error(error_msg)
        print(error_msg)

async def track_crypto(crypto_list, chat_id, time_interval, total_duration):
    start_time = datetime.now()
    end_time = start_time + timedelta(seconds=total_duration)
    tracking_active = True

    while datetime.now() < end_time and tracking_active:
        for crypto in crypto_list:
            crypto_name, crypto_price, crypto_percent_change_24h, crypto_volume_24h = get_crypto_data(crypto)
            if crypto_name is not None:
                await send_message(crypto_name, crypto_price, crypto_percent_change_24h, crypto_volume_24h, chat_id)

        tracking_active = user_data.get(chat_id, {}).get('stopped', False) != True
        await asyncio.sleep(time_interval)

def start_tracking(symbols, time_interval, chat_id, total_duration):
    asyncio.run(track_crypto(symbols, chat_id, time_interval, total_duration))

@bot.message_handler(commands=["start"])
def start(message):
    log_interaction(message)
    chat_id = message.chat.id
    if chat_id not in user_data:
        user_data[chat_id] = {}

    if 'stopped' in user_data[chat_id]:
        del user_data[chat_id]['stopped']
        user_data[chat_id].clear()  # Reset user data
        bot.send_message(chat_id, "Welcome back! Please start tracking again.")
        return

    if 'crypto_symbols' not in user_data[chat_id]:
        bot.send_message(chat_id, "Welcome to the cryptocurrency tracking bot! Which cryptocurrencies would you like to track like btc,eth,sol,ada etc..? (Enter symbols separated by commas)")
        return

    if 'time_interval' not in user_data[chat_id]:
        crypto_symbols = user_data[chat_id]['crypto_symbols']
        bot.send_message(chat_id, f"Please enter the time interval (in seconds) for tracking {', '.join(crypto_symbols)}:")
        return

    if 'total_duration' not in user_data[chat_id]:
        bot.send_message(chat_id, "Please enter the total duration (in seconds) for tracking:")
        return

    start_tracking(user_data[chat_id]['crypto_symbols'], user_data[chat_id]['time_interval'], chat_id, user_data[chat_id]['total_duration'])

@bot.message_handler(func=lambda message: message.chat.id in user_data and 'crypto_symbols' not in user_data[message.chat.id])
def get_crypto_symbols(message):
    log_interaction(message)
    chat_id = message.chat.id
    crypto_symbols = message.text.upper().split(',')
    crypto_symbols = [symbol.strip() for symbol in crypto_symbols]

    user_data[chat_id]['crypto_symbols'] = crypto_symbols
    bot.send_message(chat_id, "Please enter the time interval (in seconds) for tracking:")

@bot.message_handler(func=lambda message: message.chat.id in user_data and 'crypto_symbols' in user_data[message.chat.id] and 'time_interval' not in user_data[message.chat.id])
def get_time_interval(message):
    log_interaction(message)
    chat_id = message.chat.id
    time_interval = int(message.text)
    crypto_symbols = user_data[chat_id]['crypto_symbols']
    user_data[chat_id]['time_interval'] = time_interval
    bot.send_message(chat_id, f"Please enter the total duration (in seconds) for tracking:")

@bot.message_handler(func=lambda message: message.chat.id in user_data and 'crypto_symbols' in user_data[message.chat.id] and 'time_interval' in user_data[message.chat.id] and 'total_duration' not in user_data[message.chat.id])
def get_total_duration(message):
    log_interaction(message)
    chat_id = message.chat.id
    total_duration = int(message.text)
    user_data[chat_id]['total_duration'] = total_duration
    bot.send_message(chat_id, f"Tracking {', '.join(user_data[chat_id]['crypto_symbols'])} every {user_data[chat_id]['time_interval']} seconds for a total duration of {total_duration} seconds...")
    start_tracking(user_data[chat_id]['crypto_symbols'], user_data[chat_id]['time_interval'], chat_id, total_duration)

@bot.message_handler(commands=["stop"])
def stop_tracking(message):
    log_interaction(message)
    chat_id = message.chat.id
    if chat_id in user_data:
        user_data[chat_id]['stopped'] = True
        bot.send_message(chat_id, "Tracking stopped.")

if __name__ == "__main__":
    bot.polling(none_stop=True)
