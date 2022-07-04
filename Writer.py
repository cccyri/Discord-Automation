import threading
import requests
from random import choice, randint
from time import sleep
from threading import Thread
from json import loads
from os import system
from ctypes import windll
from sys import stderr
from loguru import logger
from urllib3 import disable_warnings
from telebot import TeleBot
from telebot import apihelper

disable_warnings()
logger.remove()
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | <cyan>{line}</cyan> - <level>{message}</level>")
clear = lambda: system('cls')
print('Cyri discord bot\n')
windll.kernel32.SetConsoleTitleW('Discord Bot')
lock = threading.Lock()

tokensfolder = str(input('TXT with Discord tokens: '))
with open(tokensfolder, 'r', encoding='utf-8') as file:
    data = [token.strip() for token in file]

if ':' not in data[0]:
    chat_id = int(input('Your ChatID: '))
else:
    chat_id = 0

use_telegram = str(input('Do you need telegram notifications? (y/N): '))

if use_telegram in ('y', 'Y'):
    bot_token = str(input('Telegram bot token: '))
    bot = TeleBot(bot_token)
    #bot.config['api_key'] = bot_token

    tg_user_id = int(input('UserID from Telegram: '))

    useproxy_telegram = str(input('Are you using proxies for Telegram? (y/N): '))
    if useproxy_telegram in ('y', 'Y'):
        proxy_type_telegram = str(input('Proxy type for Telegram (https/socks4/socks5): '))
        proxy_str_telegram = str(input('Enter proxies (ip:port or use:pass@ip:port: )'))
        apihelper.proxy = {'https':f'{proxy_type_telegram}://{proxy_str_telegram}'}


take_msgs = int(input('How to extract the messages? 1 - by default order, 2 - random order: '))

msg_input_method = int(input('How to load the messages txt: 1. One file for all accounts; 2 - Every token has its own file: '))

if msg_input_method == 1:
    current_msg_folder = str(input('Messages .txt: '))
else:
    msg_folders = {}
    for every_token in data:
        if ':' not in data[0]:
            msg_folders[str(every_token)] = str(input(f'Drag the file for {every_token}: '))
        else:
            msg_folders[str(every_token)] = str(input('Drag the file for '+every_token.split(':')[0]+': '))

delete_message_after_send = str(input('Delete the messages after sending? (y/N): '))

if delete_message_after_send in ('y', 'Y'):
    sleep_before_delete_msg = int(input('Sleep time after sending: '))

useproxy = str(input('proxy? (y/N): '))
if useproxy in ('y', 'Y'):
    proxytype = str(input('Proxy type (http/https/socks4/socks5): '))
    proxyfolder = str(input('Proxies file: '))

fist_msg_delay_type = input('Delay before the 1st message - a number or an interval (example: 0-20, or 50): ')
if '-' in fist_msg_delay_type:
    delayrange_firstmsg = fist_msg_delay_type.split('-')

every_msg_delay_type = input('Delay before the other messages - a number or an interval (example: 0-20, or 50): ')
if '-' in every_msg_delay_type:
    delayrange_everymsg = every_msg_delay_type.split('-')

sleep_when_typing = input('Time of writing imitation -  (example: 0-20, or 50): ')
if '-' in sleep_when_typing:
    range_typing_msg = sleep_when_typing.split('-')

msg_set = []
proxies_list = []
def rand_msg(current_msg_folder):
    global msg_set
    if 'msg_set' not in globals() or len(msg_set) < 1:
        msg_set = open(current_msg_folder, 'r', encoding='utf-8').read().splitlines()
    if take_msgs == 1:
        taked_msg = msg_set.pop(0)
    else:
        taked_msg = msg_set.pop(randint(0, len(msg_set)-1))
    return(taked_msg)

def getproxy():
    global proxies_list
    if 'proxies_list' not in globals() or len(proxies_list) < 1:
        proxies_list = open(proxyfolder, 'r', encoding='utf-8').read().splitlines()
    return(proxies_list.pop(0))

def check_tags(session, chat_id, ds_user_id, bot, username, token):
    last_id = None
    msg_ids = []
    all_ids = []
    while True:
        try:
            r = session.get(f'https://discord.com/api/v9/channels/{chat_id}/messages?limit=100')
            if 'retry_after' in loads(r.text):
                errortext = loads(r.text)['message']
                timetosleep = loads(r.text)['retry_after']
                logger.error(f'Error: {errortext}, sleeping {timetosleep}')
                sleep(timetosleep)
                r = session.get(f'https://discord.com/api/v9/channels/{chat_id}/messages?limit=100')
            for every_msg_id in loads(r.text):
                all_ids.append(every_msg_id['id'])
            if last_id not in all_ids:
                all_ids = []
                msg_ids = []
            if r.status_code == 200 and len(loads(r.text)) > 0:
                for usermessage in loads(r.text):
                    current_id = usermessage['id']
                    # <-- check replies
                    if 'referenced_message' in usermessage:
                        if str(ds_user_id) == str(usermessage['referenced_message']['author']['id']) and current_id not in msg_ids:
                            reply_content = usermessage['content']

                            logger.success(f'[{username}] your message has been relied to in ChatID: {chat_id}')
                            msg_ids.append(current_id)

                            bot_msg_resp = str(bot.send_message(int(tg_user_id), f'your message has been relied to\nChatID: {chat_id}\nUsername: {username}\nToken: {token}\nMsg id: {current_id}\nMsg text: {reply_content}'))
                            if 'from_user' in bot_msg_resp:
                                logger.success(f'Message sent to Telegram')
                            else:
                                logger.error(f'Message sending to Telegram error: {bot_msg_resp}')
                    # --> check replies

                    # <-- check tags
                    current_message = str(usermessage['content']).replace('\n', '').replace('\r', '')
                    if f'<@!{str(ds_user_id)}>' in current_message and current_id not in msg_ids:
                        logger.success(f'[{username}] you have been tagged in ChatID: {chat_id}')
                        msg_ids.append(current_id)
                        bot_msg_resp = str(bot.send_message(int(tg_user_id), f'you have been tagged in\nChatID: {chat_id}\nUsername: {username}\nToken: {token}\nMsg id: {current_id}\nMsg text: {current_message}'))
                        if 'from_user' in bot_msg_resp:
                            logger.success(f'Message sent to Telegram')
                        else:
                            logger.error(f'Message sending to Telegram error: {bot_msg_resp}')
                    # --> check tags
                    last_id = current_id
        except Exception as error:
            logger.error(f'[{username}] parsing error: {str(error)}')
            continue


def mainth(token, first_start, chat_id, succinit, current_msg_folder):
    if first_start == True:
        try:
            if '-' in fist_msg_delay_type:
                first_start_sleeping = randint(int(delayrange_firstmsg[0]), int(delayrange_firstmsg[1]))
            else:
                first_start_sleeping = fist_msg_delay_type
            if ':' in token:
                chat_id = token.split(':')[1]
                token = token.split(':')[0]
            session = requests.Session()
            session.headers['authorization'] = token
            if useproxy in ('y', 'Y'):
                lock.acquire()
                proxystr = getproxy()
                lock.release()
                session.proxies.update({'http': f'{proxytype}://{proxystr}', 'https': f'{proxytype}://{proxystr}'})
            r = session.get('https://discordapp.com/api/users/@me', verify=False)
            if 'username' not in loads(r.text):
                raise Exception('invalidtoken')
            username = loads(r.text)['username']
            ds_user_id = loads(r.text)['id']
            if use_telegram in ('y', 'Y'):
                Thread(target=check_tags, args=(session, chat_id, ds_user_id, bot, username, token,)).start()
            logger.info(f'First launch for [{username}], sleeping for {str(first_start_sleeping)} seconds before the 1st message')
            sleep(int(first_start_sleeping))
        except Exception as error:
            if str(error) == 'invalidtoken':
                logger.error(f'Token [{token}] is invalid')
            else:
                logger.error(f'Settings error for  [{token}]: {str(error)}')
            succinit = False
        else:
            succinit = True
    while succinit == True:
        first_start = False
        try:
            while True:
                lock.acquire()
                random_message = str(rand_msg(current_msg_folder))
                lock.release()
                json_data = {'content': str(random_message), 'tts': False}
                r = session.post(f'https://discord.com/api/v9/channels/{chat_id}/typing', verify=False)

                if '-' in sleep_when_typing:
                    time_sleep_typing = int(randint(int(range_typing_msg[0]), int(range_typing_msg[1])))
                else:
                    time_sleep_typing = int(sleep_when_typing)
                logger.info(f'Typing imitation [{username}] for {time_sleep_typing} sec')
                sleep(time_sleep_typing)
                r = session.post(
                    f'https://discord.com/api/v9/channels/{chat_id}/messages', json=json_data, verify=False)
                if 'id' in loads(r.text):
                    message_id = str(loads(r.text)['id'])
                    logger.success(f'Message [{random_message}] from [{username}] successfully sent')
                    break
                elif 'message' in loads(r.text):
                    errormsg = loads(r.text)['message']
                    if 'retry_after' in loads(r.text):
                        timesleep = float(loads(r.text)['retry_after'])
                        logger.error(f'Error: {errormsg} for [{username}], sleeping for {str(timesleep)} sec')
                        sleep(timesleep)
                    elif errormsg == 'Missing Access':
                        raise Exception('erroraccess')
                    else:
                        raise Exception(errormsg)


            if delete_message_after_send in ('y', 'Y'):
                for i in range(10):
                    logger.info(f'Sleeping for {sleep_before_delete_msg} before deletion')
                    sleep(sleep_before_delete_msg)
                    r = session.delete(f'https://discord.com/api/v9/channels/{chat_id}/messages/{message_id}', verify=False)
                    if r.status_code == 204:
                        logger.success(f'Message with ID {message_id}  containing [{random_message}] from [{username}] deleted')
                        break
                    elif 'retry_after' in loads(r.text):
                        timesleep = float(loads(r.text)['retry_after'])
                        logger.error(f'Error: {errormsg} for [{username}], sleeping {str(timesleep)} sec')
                        sleep(timesleep)
                    else:
                        logger.error(f'[{username}], error: {str(r.status_code)}, contents: {str(r.text)}')
                        sleep(3)
            if '-' in every_msg_delay_type:
                time_to_sleep_everymsg = int(randint(int(delayrange_everymsg[0]), int(delayrange_everymsg[1])))
            else:
                time_to_sleep_everymsg = int(every_msg_delay_type)
            logger.info (f'Sleeping {str(time_to_sleep_everymsg)} sec for [{username}]')
            sleep(int(time_to_sleep_everymsg))

        except Exception as error:
            if str(error) == 'erroraccess':
                logger.error(f'Error [{username}]')
                succinit = False
                break
            else:
                logger.error(f'Error for [{username}]: {str(error)}')
                pass

clear()
for _ in range(len(data)):
    while data:
        current_token = data.pop(0)
        if msg_input_method != 1:
            current_msg_folder = msg_folders[str(current_token)]
        Thread(target=mainth, args=(current_token, True, chat_id, False, current_msg_folder)).start()
