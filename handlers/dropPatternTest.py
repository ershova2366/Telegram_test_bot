import logFile
from create_bot import bot
from dbsql import BotDB
from ref import db_file

"ФАЙЛ ДЛЯ ОТПРАВКИ ШАБЛОНА excel теста файла преподавателю (program --> telegram)"

BotDB = BotDB(db_file)


def drop_file(message):
    """Функция для вывода шаблона теста"""
    if BotDB.teacher_exists(message.from_user.id):
        try:
            file = open("files/Pattern_test_Excel.xlsx", "rb")
            bot.send_document(message.chat.id, file)
        except Exception as e:
            bot.send_message(message.chat.id, "Что-то пошло не так :(")
            error_string = "Ошибка dropPatternTest.py --->drop_file: " + str(e)
            logFile.log_err(message, error_string)


def register_handlers_dropPatternTest(bot):
    bot.message_handler(commands=['pattern'])(drop_file)
