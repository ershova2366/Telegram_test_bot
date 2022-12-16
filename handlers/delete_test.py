import logFile
from create_bot import bot
from dbsql import BotDB
from ref import db_file

BotDB = BotDB(db_file)


@bot.message_handler(commands=['delete'])
def delete(message):
    """Функция обработки команды удаления теста и отправки подсказки преподавателю"""
    if BotDB.teacher_exists(message.from_user.id):
        names_table = ""
        name_table = BotDB.drop_name_test_for_teacher(message.from_user.id)
        for i in range(len(name_table)):
            names_table += str(name_table[i][0]) + "\n"
        try:
            msg = bot.send_message(message.chat.id,
                                   "Введите название теста, который хотите удалить\n"
                                   "Ваши ключи от тестов:\n" + names_table)
            bot.register_next_step_handler(msg, deleted)
        except Exception as e:
            bot.send_message(message.chat.id, "Удаление не завершено")
            error_string = "Ошибка delete_test.py --->delete: " + str(e)
            logFile.log_err(message=message.chat.id, err=error_string)


def deleted(message):
    """Функция удаления теста"""
    name_table = message.text
    try:
        BotDB.delete_test(name_table)

        bot.send_message(message.chat.id, "Удаление успешно завершено")
    except Exception as e:
        bot.send_message(message.chat.id, "Удаление не завершено!")
        error_string = "Ошибка delete_test.py --->deleted: " + str(e)
        logFile.log_err(message=message.chat.id, err=error_string)


def register_handlers_delete_test(bot):
    bot.message_handler(content_types=['delete'])(delete)
