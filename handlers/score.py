import logFile
from dbsql import BotDB
from create_bot import bot
from ref import db_file

"ФАЙЛ ДЛЯ ВЫВОДА баллов пройденных теста  (DB --> telegram)"

BotDB = BotDB(db_file)


def drop_score(message):
    try:
        if BotDB.teacher_exists(message.from_user.id):
            names_table = ""
            name_table = BotDB.drop_name_test_for_teacher(message.from_user.id)
            for i in range(len(name_table)):
                names_table += str(name_table[i][0]) + "\n"

            bot.send_message(message.chat.id,
                             "Введите ключ от теста для получения баллов\nВаши ключи от тестов:\n" + names_table)
            bot.register_next_step_handler(message, print_score_for_teacher)
        else:
            bot.send_message(message.chat.id, "Введите ключ от теста для получения баллов")
            bot.register_next_step_handler(message, print_score_for_teacher)
    except Exception as e:
        bot.send_message(message.chat.id, "Что-то пошло не так!")
        error_string = "Ошибка score.py --->drop_score: " + str(e)
        logFile.log_err(message, error_string)


@bot.message_handler(commands=['my_score'])
def score_for_user(message):
    """Функция для отправки подсказки пользователю для получения персональных баллов за тест"""
    bot.send_message(message.chat.id, "Введите название теста, баллы за который хотите посмотреть")
    bot.register_next_step_handler(message, print_score_for_user)


def print_score_for_user(message):
    """Функция для вывода персональных баллов за тест"""
    try:
        max_balls = BotDB.max_question_number(message.text)
        name_table = message.text
        name_table_score = name_table + "_score"
        score = "Название теста: " + message.text + "\n" + "Максимальное количество баллов за тест: " + str(
            max_balls[0]) + "\n"

        if BotDB.check_test_in_db(name_table_score):
            scor = BotDB.drop_score_for_user(name_table, message.chat.id, )
            for i in range(len(scor)):
                for j in range(1):
                    if j == 0:

                        score += "БАЛЛЫ ЗА ТЕСТ: " + str(scor[i][j])
                    else:
                        score += str(scor[i][j]) + " "
                score += "\n"

            bot.send_message(message.chat.id, f" {score}")
        else:
            bot.send_message(message.chat.id, "Такого теста не существует")
    except Exception as e:
        bot.send_message(message.chat.id, "Что-то пошло не так!")
        error_string = "Ошибка score.py --->print_score_for_user: " + str(e)
        logFile.log_err(message, error_string)


def print_score_for_teacher(message):
    """Функция для вывода всех баллов учеников за тест"""
    try:
        max_balls = BotDB.max_question_number(message.text)
        score = "Название теста: " + message.text + "\n" + "Максимальное количество баллов за тест: " + str(
            max_balls[0]) + "\n"
        name_table = message.text
        name_table_score = name_table + "_score"
        if BotDB.check_test_in_db(name_table_score):
            scor = BotDB.drop_score_for_teacher(name_table)
            for i in range(len(scor)):
                for j in range(4):
                    if j == 3:
                        score += "БАЛЛЫ ЗА ТЕСТ: " + str(scor[i][j])
                    else:
                        score += str(scor[i][j]) + " "
                score += "\n"

            bot.send_message(message.chat.id, f" {score}")
        else:
            bot.send_message(message.chat.id, "Такого теста не существует")
    except Exception as e:
        bot.send_message(message.chat.id, "Что-то пошло не так!")
        error_string = "Ошибка score.py --->print_score_for_teacher: " + str(e)
        logFile.log_err(message, error_string)


def register_handlers_score(bot):
    bot.message_handler(commands=['score'])(drop_score)
