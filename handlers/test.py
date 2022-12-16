from telebot import types
import logFile
from dbsql import BotDB
from create_bot import bot
from ref import db_file
from logFile import log

"ФАЙЛ ДЛЯ ВЫВОДА тестов (DB --> telegram)"

BotDB = BotDB(db_file)

# Словарь для передачи данных через функции
test_dict_message_to_edit = {}  # словарь, где хранятся пары id пользователя - изменяемое сообщение
dict_id_question = {}  # словарь, где хранятся пары id пользователя - id вопроса
dict_balls = {}  # словарь, где хранятся пары id пользователя - набранные баллы
dict_text = {}  # словарь, где хранятся пары id пользователя - текст сообщения
dict_drop_test_calls = {}  # содержит количество вводов пользователем названия теста


# ======================ТЕСТ==============================


def get_test(message):
    """Начало работы с тестом, функция получения названия теста"""
    log(message)
    try:
        if (BotDB.teacher_exists(message.from_user.id)) or (BotDB.user_exists(message.from_user.id)):
            # проверка на наличие проходящего тест в базе данных
            bot.send_message(message.chat.id, "Введите название теста:")
            dict_drop_test_calls[message.chat.id] = 0  # начальное значение счётчика баллов
            bot.register_next_step_handler(message,
                                           drop_test)
            # метод позволяющий передать введенное сообщение внутри обработчика в функцию drop_test
        else:
            bot.send_message(message.chat.id, "Для прохождения теста пройдите регистрацию: введите /start")
            # отправка пользователю вспомогательного сообщения
    except Exception as e:
        bot.send_message(message.chat.id, "Что-то пошло не так :(")
        # отправка пользователю сообщения об ошибке
        error_string = "Ошибка test.py --->get_test: " + str(e)
        logFile.log_err(message, error_string)


def print_test(message_chat_id, name_table, id_question):
    """Функция формирования вопроса с ответами на экране + проверка баллов"""
    try:
        test = BotDB.drop_test(name_table, id_question)
        test_out = []
        for i in test[0]:
            test_out.append(i)
        test_out_num_q = "Вопрос №" + str(id_question) + "\n" + str(test_out[0])
        # строка содержащая номер и текст вопроса
        keyboard_button_text_1 = "A" + ":" + str(id_question) + ":" + name_table  # создание текста 1 кнопки
        keyboard_button_text_2 = "B" + ":" + str(id_question) + ":" + name_table  # создание текста 2 кнопки
        keyboard_button_text_3 = "C" + ":" + str(id_question) + ":" + name_table  # создание текста 3 кнопки
        keyboard_button_text_4 = "D" + ":" + str(id_question) + ":" + name_table  # создание текста 4 кнопки
        markup = types.InlineKeyboardMarkup()  # объявление кнопок шаблона InlineKeyboardMarkup
        # https://surik00.gitbooks.io/aiogram-lessons/content/chapter5.html
        # https://qna.habr.com/q/837981
        # InlineKeyboardMarkup — клавиатура привязанная к сообщению, использующая обратный вызов (callback_data)
        markup.add(types.InlineKeyboardButton(test_out[1], callback_data=keyboard_button_text_1))
        markup.add(types.InlineKeyboardButton(test_out[2], callback_data=keyboard_button_text_2))
        markup.add(types.InlineKeyboardButton(test_out[3], callback_data=keyboard_button_text_3))
        markup.add(types.InlineKeyboardButton(test_out[4], callback_data=keyboard_button_text_4))
        # добавление четырёх кнопок в клавиатуру
        # markup.add(types.InlineKeyboardButton(ТЕКСТ КНОПКИ, callback_data=ТО ЧТО ПОЛУЧИТ КОЛБЕК))
        # callback_data--------->@bot.callback_query_handler
        test_dict_message_to_edit[message_chat_id] = bot.send_message(message_chat_id, test_out_num_q,
                                                                      reply_markup=markup)
        # вносим в словарь сообщение, которое в дальнейшем будем изменять
    except Exception as e:
        bot.send_message(message_chat_id, "Что-то пошло не так :(")
        # отправка пользователю сообщения об ошибке
        error_string = "Ошибка test.py --->print_test: " + str(e)
        logFile.log_err(message_chat_id, error_string)


def drop_test(message):
    """ Функция вывода теста на экран, нужна для вывода первого вопроса """
    dict_balls[message.chat.id] = 0   # начальное значение счётчика баллов
    name_table = message.text  # принимаем сообщение, как переменную с названием таблицы
    dict_id_question[message.chat.id] = 1  # начальный индекс вопроса

    try:
        print_test(message.chat.id, name_table, dict_id_question.get(message.chat.id))
        # вызываем функцию формирования вопросов на экране

    except Exception as e:  # теста нет в базе
        dict_drop_test_calls[message.chat.id] += 1  # увеличиваем кол-во потраченных попыток на 1
        if dict_drop_test_calls[message.chat.id] < 4:  # ограничение на количество вводов названия теста
            msg = bot.send_message(message.chat.id,
                                   "Такого теста не существует" + "\n"
                                   + "Уточните название теста у преподавателя"
                                   + "и повторите ввод" + "\n" + "Осталось попыток: "
                                   + str(4 - dict_drop_test_calls[message.chat.id]))
            # отправка вспомогательного сообщения пользователю
            bot.register_next_step_handler(msg, drop_test)  # ожидает сообщение пользователя и вызывает drop_test
        else:  # кол-во вводов превысило максимально разрешённое
            bot.send_message(message.chat.id, "Для ознакомления с основными функциями бота введите\n/help")
            # отправка пользователю вспомогательного сообщения
            del dict_drop_test_calls[message.chat.id]


def callback_inline(call):
    """Функция переключения вопроса, формирования результата, подсчёта баллов"""
    try:
        bot.answer_callback_query(call.id)  # убирает состояние загрузки кнопки после нажатия на неё
        user_list = call.data.split(':')
        ans = "answer" + user_list[0]  # создаём строку чтобы по ней вытащить ячейку из sql таблицы
        answer = BotDB.user_answer(ans, user_list[1], user_list[2])[0]  # ответ пользователя
        max = BotDB.max_question_number(user_list[2])
        max_question = max[0]  # максимальное число вопросов в тесте
        markup = types.InlineKeyboardMarkup()  # объявление кнопок шаблона InlineKeyboardMarkup
    except Exception as e:
        bot.send_message(call.message.chat.id, "Что-то пошло не так :(")
        # отправка пользователю сообщения об ошибке
        error_string = "Ошибка test.py --->callback_inline: " + str(e)
        logFile.log_err(call.message.chat.id, error_string)

    try:
        name_table = user_list[2]  # имя переданной бд
        test = BotDB.drop_test(name_table, dict_id_question.get(call.message.chat.id))
        user_answer = [test[0][0]]
        k = 1
        while k != 5:
            # создаю список user_answer, который присылается пользователю, как сообщение после нажатия на кнопку ответа
            if test[0][k] == answer:
                # проверка правильный ли ответ пользователя
                if test[0][k] == test[0][5]:  # ответ пользователя верный
                    user_answer.append(test[0][k] + " ✅")  # строка с правильным ответом
                    dict_balls[call.message.chat.id] = dict_balls.get(call.message.chat.id) + 1
                else:  # ответ пользователя неверный
                    user_answer.append(test[0][k] + " ❌")  # строка с неправильным ответом
            else:  # варианты ответов, невыбранные пользователем
                user_answer.append(test[0][k])
            k += 1
        dict_text[call.message.chat.id] = "Вопрос № " + str(dict_id_question.get(call.message.chat.id)) + "\n" \
                                          + str(user_answer[0]) + "\n" + str(user_answer[1]) + "\n" \
                                          + (user_answer[2]) + "\n" + str(user_answer[3]) + "\n" + str(user_answer[4])
        # формирование текста сообщения, отправляемого пользователю, после нажатия на кнопку
    except Exception as e:
        bot.send_message(call.message.chat.id, "Что-то пошло не так :(")
        # отправка пользователю сообщения об ошибке
        error_string = "Ошибка test.py --->callback_inline: " + str(e)
        logFile.log_err(call.message.chat.id, error_string)

    message_to_edit = test_dict_message_to_edit.get(call.message.chat.id)
    if dict_id_question.get(call.message.chat.id) < max_question:  # вывод результата вопроса
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=message_to_edit.id,
                              text=dict_text.get(call.message.chat.id))
        # изменение сообщения с вопросом теста на его результат (с отметкой правильности ответа пользователя)
        dict_id_question[call.message.chat.id] = dict_id_question.get(call.message.chat.id) + 1
        # переход к следующему вопросу
        if dict_id_question.get(call.message.chat.id) != 1:  # вывод следующего вопроса теста
            print_test(call.message.chat.id, user_list[2], dict_id_question.get(call.message.chat.id))

    elif dict_id_question.get(call.message.chat.id) == max_question:  # вывод результата всего теста
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=message_to_edit.id,
                              text=dict_text.get(call.message.chat.id))
        # замена сообщения с последним вопросом, на его результат
        # формирование результатов теста
        if (dict_balls.get(call.message.chat.id) > 10) and (dict_balls.get(call.message.chat.id) < 20):
            bal = " баллов"
        else:
            if dict_balls.get(call.message.chat.id) % 10 == 1:
                bal = " балл"
            elif (dict_balls.get(call.message.chat.id) % 10 == 2) \
                    or (dict_balls.get(call.message.chat.id) % 10 == 3) \
                    or (dict_balls.get(call.message.chat.id) % 10 == 4):
                bal = " балла"
            else:
                bal = " баллов"
        dict_text[call.message.chat.id] = "Результат теста: " + "\n" \
                                          + str(dict_balls.get(call.message.chat.id)) + bal + \
                                          " из " + str(max_question) + "\n" \
                                          + "Для ознакомления с основными функциями бота введите\n/help"
        # формирование текста сообщения с результатом теста
        try:
            BotDB.insert_score_test(name_table, call.message.chat.id, dict_balls.get(call.message.chat.id))
            # внесение результата ученика в БД
            bot.send_message(call.message.chat.id, dict_text.get(call.message.chat.id),
                             reply_markup=markup)  # отправка сообщения с результатом пользователю
            del dict_id_question[call.message.chat.id]
            del dict_balls[call.message.chat.id]
            del test_dict_message_to_edit[call.message.chat.id]
            del dict_text[call.message.chat.id]
        except Exception as e:
            bot.send_message(call.message.chat.id, "Что-то пошло не так :(")
            # отправка пользователю сообщения об ошибке
            error_string = "Ошибка test.py --->callback_inline: " + str(e)
            logFile.log_err(call.message.chat.id, error_string)


def register_handlers_test(bot):
    bot.message_handler(commands=['test'])(get_test)
