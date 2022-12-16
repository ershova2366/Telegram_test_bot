import telebot  # https://pypi.org/project/pyTelegramBotAPI/0.3.0/

import logFile
from ref import token

"ФАЙЛ ДЛЯ ПОДЛЮЧЕНИЯ бота (program --> telegram)"

try:
    bot = telebot.TeleBot(token)  # ссылка на токин для соединения с ботом
except Exception as e:
    error_string = "Ошибка create_bot.py --->ОШИБКА ПРИ СОЗДАНИИ БОТА!: " + str(e)
    logFile.log_err(err=error_string)
