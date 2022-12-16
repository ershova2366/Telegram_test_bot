import logFile
from create_bot import bot
from dbsql import BotDB
from ref import db_file
from handlers import importExcel

BotDB = BotDB(db_file)


@bot.message_handler(commands=['change'])
def change(message):
    """Функция обработки изменения теста и отправки подсказки преподавателю"""
    if BotDB.teacher_exists(message.from_user.id):
        msg = bot.send_message(message.chat.id,
                               "Отправьте изменённый exel-файл с этим тестом, название должно быть прежнее")
        try:
            bot.register_next_step_handler(msg, ch)
        except Exception as e:
            error_string = "Ошибка change_test.py --->change: " + str(e)
            logFile.log_err(message=message.chat.id, err=error_string)
            bot.send_message(message.chat.id, "Изменения не завершены")


def ch(message):
    """Функция изменения теста"""
    try:
        name_file = message.document.file_name  # Название файла в формат nnn.xxx
        name_file_s = str(name_file).split(".")
        BotDB.delete_test(name_file_s[0])  # удаляем существующий тест с таким названием
        importExcel.read_excel(message)  # заменить его на новый
        bot.send_message(message.chat.id,
                         "Изменения успешно завершены")
    except Exception as e:
        error_string = "Ошибка change_test.py --->ch: " + str(e)
        logFile.log_err(message=message.chat.id, err=error_string)
        bot.send_message(message.chat.id, "Изменения не завершены")


def register_handlers_change_test(bot):
    bot.message_handler(content_types=['change'])(change)
