import re
from telebot import types
import logFile
from dbsql import BotDB
from create_bot import bot
from ref import db_file
from ref import password
from logFile import log
from handlers import test

"ФАЙЛ ДЛЯ РЕГИСТРАЦИИ пользователей и преподавателей (telegram --> DB)"

BotDB = BotDB(db_file)

# ----------------------РЕГИСТРАЦИЯ-------------------------------------------

# Словарь для передачи данных через функции
dict_name_user_for_users = {}  # словарь, где хранятся пары id пользователя - зарегистрированное имя
dict_surname_user_for_users = {}  # словарь, где хранятся пары id пользователя - зарегистрированная фамилия
dict_group_user_for_users = {}  # словарь, где хранятся пары id пользователя - зарегистрированная группа

dict_name_teacher_for_teacher = {}  # словарь, где хранятся пары id преподавателя - зарегистрированное имя
dict_surname_teacher_for_teacher = {}  # словарь, где хранятся пары id преподавателя - зарегистрированная фамилия
dict_teacher_patronymic_for_teacher = {}  # словарь, где хранятся пары id преподавателя - зарегистрированное отчество

dict_get_password_calls = {}  # словарь, где хранятся пары id преподавателя - количество попыток ввода пароля

reg_dict_message_to_edit = {}  # словарь, где хранятся пары id пользователя - изменяемое сообщение


def get_user_text(message):
    """Переработка текста отправленного кнопкой и запуск нужного процесса регистрации"""
    log(message)
    get_message = message.text.strip().lower()
    if get_message == "зарегистрироваться как студент":  # регистрация для студентов
        bot.send_message(message.chat.id,
                         "Введите ваше имя:",
                         reply_markup=types.ReplyKeyboardRemove())  # отправка пользователю сообщения в чат
        bot.register_next_step_handler(message, check_name)
    elif get_message == "зарегистрироваться как преподаватель":  # регистрация для преподавателей
        dict_get_password_calls[message.chat.id] = 0  # начальное значение счётчика количества введённых паролей
        bot.send_message(message.chat.id,
                         "Введите код доступа:",
                         reply_markup=types.ReplyKeyboardRemove())
        # отправка пользователю сообщения в чат с просьбой ввода пароля
        bot.register_next_step_handler(message,
                                       get_password)  # ждёт сообщение от пользователя, передаёт его в get_password
    elif get_message == 'мой id':  # узнать свой id
        bot.send_message(message.chat.id,
                         message.from_user.id)  # отправка сообщения с id пользователя
    else:  # было введено сообщение, не являющееся командой бота
        bot.send_message(message.chat.id,
                         "Не понял вас \nДля знакомства с основными командами бота введите /help")
        # отправка вспомогательного сообщения пользователю


def check_text(text):
    """Функция проверки текста на соответствие общему шаблону"""
    regex = re.compile(r'([А-Яа-яЁё]+)')  # Регулярное выражение. Текст состоит только из букв русского алфавита
    a = re.fullmatch(regex, text)  # проверка на соответствие текста регулярному выражению
    return bool(a)  # возвращаем значение True(да) или False(нет)


def data(message):
    """Функция вывода зарегистрированные данных пользователя в настоящий момент"""
    try:
        user_data = BotDB.get_user(message.chat.id)  # получаем все данные о пользователе из БД
        mes_user = f"Ваши данные: \n" \
                   f"Ваше имя: {user_data[0][2].title()} \n" \
                   f"Ваша фамилия: {user_data[0][3].title()} \n" \
                   f"Ваша группа: {user_data[0][4].title()}"
        # формируем текст сообщения пользователю с его данными
        bot.send_message(message.chat.id, mes_user)  # отправляем пользователю сообщение с его данными
    except Exception as e:
        bot.send_message(message.chat.id, "Что-то пошло не так :(")
        error_string = "Ошибка registration.py --->data: " + str(e)
        logFile.log_err(message, error_string)


def check_name(message):
    """Функция проверки имени на соответствие шаблону, при несовпадении требует повторный ввод"""
    log(message)
    name = str(message.text)  # получаем введённое имя пользователя
    if check_text(name):  # имя соответствует шаблону, вносим в БД
        try:
            if BotDB.user_exists(message.from_user.id):  # для изменения зарегистрированных данных
                BotDB.update_user_name(message)  # обновляем значение поля имя пользователя в БД
                bot.send_message(message.chat.id, "Изменения успешно внесены!")  # отправка юзеру сообщения об успехе
                data(message)  # вывод данных пользователя
                d = {"Имя": "имя", "Фамилию": "фамилия",
                     "Группу": "группа", "Завершить изменения": "стоп"}  # словарь для формирования кнопок
                message_to_edit = bot.send_message(message.chat.id,
                                                   text="Что бы вы хотели изменить?",
                                                   reply_markup=weather_key(d),
                                                   parse_mode='Markdown')  # отправка сообщения с кнопками
                reg_dict_message_to_edit[message.chat.id] = message_to_edit
                # внесение сообщения для редактирования в словарь
            else:  # для внесения данных регистрации
                add_name_user(message)
        except Exception as e:
            bot.send_message(message.chat.id, "Что-то пошло не так :(")
            error_string = "Ошибка registration.py --->check_name: " + str(e)
            logFile.log_err(message, error_string)

    else:  # name не соответствует шаблону, требуем повторный ввод
        bot.send_message(message.chat.id,
                         "Неверный формат имени, повторите ввод")
        # отправка пользователю сообщения с просьбой повторного ввода
        bot.register_next_step_handler(message,
                                       check_name)  # ожидание сообщения от пользователя и передача его в check_name


# https://habr.com/ru/post/349860/


def add_name_user(message):
    """Функция утверждения имени, просит ввести фамилию и отправляет его на проверку"""
    log(message)
    name_user = message.text  # получения текста сообщения
    dict_name_user_for_users[message.from_user.id] = name_user  # внесение имени пользователя в словарь
    bot.send_message(message.chat.id,
                     "Введите вашу фамилию:")  # отправка пользователю сообщения с просьбой ввода фамилии
    bot.register_next_step_handler(message, check_surname)  # ждёт сообщение от пользователя, передаёт его check_surname


def check_surname(message):
    """Функция проверяет фамилию на соответствие шаблону, просит повторный ввод, если фамилия некорректна"""
    log(message)
    surname = str(message.text)  # получаем введённую фамилию пользователя
    if check_text(surname):  # фамилия соответствует шаблону, вносим в БД
        try:
            if BotDB.user_exists(message.from_user.id):  # для зарегистрированных пользователей
                BotDB.update_user_surname(message)  # обновление данных в БД
                bot.send_message(message.chat.id, "Изменения успешно внесены!")  # отправка юзеру сообщения
                data(message)  # вывод данных о пользователе
                d = {"Имя": "имя", "Фамилию": "фамилия",
                     "Группу": "группа", "Завершить изменения": "стоп"}  # словарь с текстом кнопок клавиатуры
                message_to_edit = bot.send_message(message.chat.id,
                                                   text="Что бы вы хотели изменить?",
                                                   reply_markup=weather_key(d),
                                                   parse_mode='Markdown')
                # отправка пользователю сообщения с предложением внести изменения
                reg_dict_message_to_edit[message.chat.id] = message_to_edit
                # внесение в словарь сообщения для редактирования
            else:  # для незарегистрированных пользователей
                add_surname_user(message)  # при соответствии фамилии шаблону, внести фамилию в БД
        except Exception as e:
            bot.send_message(message.chat.id, "Что-то пошло не так :(")
            error_string = "Ошибка registration.py --->check_surname: " + str(e)
            logFile.log_err(message, error_string)

    else:  # фамилия не соответствует шаблону, требуем повторный ввод
        bot.send_message(message.chat.id,
                         "Неверный формат фамилии, повторите ввод")
        # отправка пользователю сообщения с просьбой повторного ввода фамилии
        bot.register_next_step_handler(message,
                                       check_surname)  # ждёт сообщение от пользователя и передаёт его check_surname


def add_surname_user(message):
    """Функция утверждает фамилию, просит ввести номер группы"""
    log(message)
    surname_user = message.text  # получаем текст сообщения
    dict_surname_user_for_users[message.from_user.id] = surname_user  # вносим фамилию пользователя в словарь
    bot.send_message(message.chat.id,
                     "Введите номер группы:")
    # отправка пользователю сообщения с просьбой ввода группы
    bot.register_next_step_handler(message,
                                   add_group_user)  # ждёт сообщение от пользователя и передаёт его в add_group_user


def up_group_user(message):
    """Функция обновляет группу, предлагает внести какие-либо изменения или завершить их"""
    try:
        BotDB.update_user_group(message)  # обновляем группу пользователя
        bot.send_message(message.chat.id, "Изменения успешно внесены!")  # сообщаем пользователю об успешных изменениях
        data(message)  # вывод данных о пользователе
        d = {"Имя": "имя", "Фамилию": "фамилия",
             "Группу": "группа", "Завершить изменения": "стоп"}  # словарь с текстом кнопок клавиатуры
        message_to_edit = bot.send_message(message.chat.id,
                                           text="Что бы вы хотели изменить?",
                                           reply_markup=weather_key(d),
                                           parse_mode='Markdown')
        # отправка пользователю сообщения с предложением внести изменения
        reg_dict_message_to_edit[message.chat.id] = message_to_edit  # внесение в словарь сообщения для изменения
    except Exception as e:
        bot.send_message(message.chat.id, "Что-то пошло не так :(")
        error_string = "Ошибка registration.py --->up_group_user: " + str(e)
        logFile.log_err(message, error_string)


def weather_key(dictionary):
    """Функция, отвечающая за изменение клавиатуры в зависимости от аргумента функции"""
    weather = types.InlineKeyboardMarkup(row_width=2)  # создаём шаблон встроенной клавиатуры для сообщения
    for key in dictionary:  # создание кнопок с названиями из словаря
        weather.add(types.InlineKeyboardButton(text=key, callback_data=dictionary[key]))
        # добавляем кнопку в клавиатуру
    return weather  # возвращает клавиатуру для сообщения


def add_group_user(message):
    """Функция утверждает группу, завершает процесс регистрации"""
    log(message)

    d = {"Завершить процесс регистрации": "завершить",
         "Изменить данные": "изменить"}  # словарь с текстом кнопок клавиатуры

    group_user = message.text  # получаем текст сообщения
    dict_group_user_for_users[message.from_user.id] = group_user  # передаём группу пользователя в словарь
    # reg_list[name_user,surname_user,group_user]

    name_user = str(dict_name_user_for_users.get(message.chat.id))  # получаем имя пользователя из словаря
    surname_user = str(dict_surname_user_for_users.get(message.chat.id))  # получаем фамилию пользователя из словаря
    group_user = str(dict_group_user_for_users.get(message.chat.id))  # получаем группу пользователя из словаря

    mes = f"Ваше имя: {name_user.title()} \n" \
          f"Ваша фамилия: {surname_user.title()} \n" \
          f"Ваша группа: {group_user.title()} \n"
    # формируем текст сообщения пользователю с его данными
    reg_dict_message_to_edit[message.chat.id] = bot.send_message(message.chat.id,
                                                                 "Проверьте данные на корректность\n" + mes +
                                                                 "❗После завершения процесса регистрации " +
                                                                 "данные изменить невозможно",
                                                                 reply_markup=weather_key(d))

    if not BotDB.user_exists(message.from_user.id):  # проверка на отсутствие пользователя в БД
        try:
            name_user = str(dict_name_user_for_users.get(message.from_user.id))
            # получаем имя пользователя из словаря
            surname_user = str(dict_surname_user_for_users.get(message.from_user.id))
            # получаем фамилию пользователя из словаря
            group_user = str(dict_group_user_for_users.get(message.from_user.id))
            # получаем группу пользователя из словаря
            BotDB.add_user(message.from_user.id, name_user, surname_user, group_user)  # внесение юзера в БД
        except Exception as e:
            bot.send_message(message.chat.id, "Что-то пошло не так :(")
            error_string = "Ошибка registration.py --->add_group_user: " + str(e)
            logFile.log_err(message, error_string)
    else:  # пользователь присутствует в БД (уже зарегистрирован)
        bot.send_message(message.chat.id,
                         "Вы уже зарегистрированы")  # отправка сообщения в случае, если пользователь уже есть в БД


# -------------------------------------------РЕЖИМ ПРЕПОДАВАТЕЛЯ-------------------------------------------


def get_password(message):
    """Функция проверяет код преподавателя, при совпадении начинает процесс регистрации"""
    log(message)
    dict_get_password_calls[message.chat.id] += 1  # увеличиваем счётчик ввода пароля на 1
    get_message = message.text.strip().lower()
    if get_message == password:  # если пароль верный, то начинаем запрашивать данные для регистрации
        bot.send_message(message.chat.id, "Введите вашу фамилию:",
                         reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, check_teacher_surname)  # ждём смс, передаём его в check_teacher_surname
    else:  # пароль неверный, требуем повторный ввод, дано 4 попытки
        if dict_get_password_calls[message.chat.id] < 4:
            bot.send_message(message.chat.id,
                             "Неверный код \nПовторите попытку\nОсталось попыток: "
                             + str(4 - dict_get_password_calls[message.chat.id]))
            bot.register_next_step_handler(message,
                                           get_password)  # ждём смс, передаём его в get_password
        else:  # количество попыток исчерпано, выход на старт регистрации
            bot.send_message(message.chat.id,
                             "Неверный код \n Начните регистрацию заново, введите /start")
            del dict_get_password_calls[message.chat.id]


def data_teacher(message):
    """Функция выводит зарегистрированные данные преподавателя в настоящий момент"""
    try:
        teacher_data = BotDB.get_teacher(message.chat.id)  # получаем зарегистрированные данные преподавателя из БД
        mes_user = f"Ваши данные: \n" \
                   f"Ваша фамилия: {teacher_data[0][2].title()} \n" \
                   f"Ваше имя: {teacher_data[0][3].title()} \n" \
                   f"Ваше отчество: {teacher_data[0][4].title()}"
        # формируем текст сообщения пользователю с его данными
        bot.send_message(message.chat.id, mes_user)  # отправляем преподавателю его зарегистрированные данные
    except Exception as e:
        bot.send_message(message.chat.id, "Что-то пошло не так :(")
        error_string = "Ошибка registration.py --->data_teacher: " + str(e)
        logFile.log_err(message, error_string)


def check_teacher_surname(message):
    """Функция проверяет фамилию на соответствие шаблону, просит повторный ввод, если фамилия некорректна"""
    log(message)
    teacher_surname = str(message.text)  # получаем текст сообщения
    if check_text(teacher_surname):  # при соответствии фамилии шаблону
        try:
            if BotDB.teacher_exists(message.from_user.id):  # при наличии преподавателя в БД
                BotDB.update_teacher_surname(message)  # обновляем фамилию преподавателя
                data_teacher(message)  # вывод зарегистрированных данных пользователя
                bot.send_message(message.chat.id, "Изменения успешно внесены!")  # отправка сообщения преподавателю
                d = {"Фамилию": "п_фамилия", "Имя": "п_имя", "Отчество": "п_отчество", "Завершить изменения": "стоп"}
                # словарь с текстом кнопок клавиатуры
                message_to_edit = bot.send_message(message.chat.id,
                                                   text="Что бы вы хотели изменить?",
                                                   reply_markup=weather_key(d),
                                                   parse_mode='Markdown')  # отправка сообщения с клавиатурой
                # отправка пользователю сообщения с предложением внести изменения
                reg_dict_message_to_edit[message.chat.id] = message_to_edit  # добавление сообщения в словарь
            else:  # если преподаватель есть в БД
                add_teacher_surname(message)  # добавление фамилии преподавателя
        except Exception as e:
            bot.send_message(message.chat.id, "Что-то пошло не так :(")
            error_string = "Ошибка registration.py --->check_teacher_surname: " + str(e)
            logFile.log_err(message, error_string)

    else:
        bot.send_message(message.chat.id,
                         "Неверный формат фамилии, повторите ввод")   # отправка сообщения с просьбой повторного ввода
        bot.register_next_step_handler(message,
                                       check_teacher_surname)  # ждём смс, передаём его в check_teacher_surname


def add_teacher_surname(message):
    """Функция утверждает фамилию, просит ввести имя и отправляет его на проверку"""
    log(message)
    teacher_surname = message.text  # получаем текст сообщения
    dict_surname_teacher_for_teacher[message.from_user.id] = teacher_surname  # вносим фамилию в словарь
    bot.send_message(message.chat.id,
                     "Введите ваше имя:")  # отправка сообщения с просьбой ввода имени
    bot.register_next_step_handler(message,
                                   check_teacher_name)  # ждём сообщения, передаём его в check_teacher_name


def check_teacher_name(message):
    """Функция проверяет имя на соответствие шаблону, просит повторный ввод, если имя некорректно"""
    log(message)
    teacher_name = str(message.text)  # получаем текст сообщения
    if check_text(teacher_name):  # при соответствии имени шаблону
        try:
            if BotDB.teacher_exists(message.from_user.id):  # если преподаватель есть в БД
                BotDB.update_teacher_name(message)  # обновляем имя преподавателя в БД
                data_teacher(message)  # вывод зарегистрированных данных пользователя
                bot.send_message(message.chat.id, "Изменения успешно внесены!")  # отправка юзеру сообщения
                d = {"Фамилию": "п_фамилия", "Имя": "п_имя", "Отчество": "п_отчество", "Завершить изменения": "стоп"}
                # словарь с текстом кнопок клавиатуры
                message_to_edit = bot.send_message(message.chat.id,
                                                   text="Что бы вы хотели изменить?",
                                                   reply_markup=weather_key(d),
                                                   parse_mode='Markdown')  # отправка сообщения с клавиатурой
                reg_dict_message_to_edit[message.chat.id] = message_to_edit  # добавление сообщения в словарь
            else:
                add_teacher_name(message)  # добавление имени преподавателя
        except Exception as e:
            bot.send_message(message.chat.id, "Что-то пошло не так :(")
            error_string = "Ошибка registration.py --->check_teacher_name: " + str(e)
            logFile.log_err(message, error_string)

    else:  # имя не соответствует шаблону
        bot.send_message(message.chat.id,
                         "Неверный формат имени, повторите ввод")  # отправка сообщения с просьбой повторного ввода
        bot.register_next_step_handler(message,
                                       check_teacher_name)  # ждём сообщения, передаём его в check_teacher_name


def add_teacher_name(message):
    """Функция утверждает имя, просит ввести отчество и отправляет его на проверку"""
    log(message)
    teacher_name = message.text
    dict_name_teacher_for_teacher[message.from_user.id] = teacher_name  # добавление имени пользователя в словарь
    bot.send_message(message.chat.id,
                     "Введите ваше отчество:")  # отправка сообщения преподавателю с просьбой ввести отчество
    bot.register_next_step_handler(message,
                                   check_teacher_patronymic)  # ждём сообщения, передаём его в check_teacher_patronymic


def check_teacher_patronymic(message):
    """Функция проверяет отчество на соответствие шаблону, просит повторный ввод, если отчество некорректно"""
    log(message)
    teacher_patronymic = str(message.text)  # получаем текст сообщения
    if check_text(teacher_patronymic):  # при соответствии отчества шаблону
        try:
            if BotDB.teacher_exists(message.from_user.id):  # если преподаватель есть в БД
                BotDB.update_teacher_patronymic(message)  # обновляем отчество преподавателя в БД
                data_teacher(message)  # вывод зарегистрированных данных пользователя
                bot.send_message(message.chat.id, "Изменения успешно внесены!")  # отправка юзеру сообщения об успехе
                d = {"Фамилию": "п_фамилия", "Имя": "п_имя", "Отчество": "п_отчество", "Завершить изменения": "стоп"}
                # словарь с текстом кнопок клавиатуры
                message_to_edit = bot.send_message(message.chat.id,
                                                   text="Что бы вы хотели изменить?",
                                                   reply_markup=weather_key(d),
                                                   parse_mode='Markdown')    # отправка сообщения с клавиатурой
                reg_dict_message_to_edit[message.chat.id] = message_to_edit  # добавление имени пользователя в словарь
            else:
                add_teacher_patronymic(message)  # добавление отчества преподавателя
        except Exception as e:
            bot.send_message(message.chat.id, "Что-то пошло не так :(")
            error_string = "Ошибка registration.py --->check_teacher_patronymic: " + str(e)
            logFile.log_err(message, error_string)
    else:
        bot.send_message(message.chat.id,
                         "Неверный формат отчества, повторите ввод")
        bot.register_next_step_handler(message,
                                       check_teacher_patronymic)
        # ждём сообщение от пользователя, передаём его в check_teacher_patronymic


def add_teacher_patronymic(message):
    """Функция утверждает отчество, завершает процесс регистрации"""
    log(message)
    d = {"Завершить процесс регистрации": "п_завершить", "Изменить данные": "п_изменить"}
    # словарь с текстом кнопок клавиатуры
    teacher_patronymic = message.text  # получаем текст сообщения
    dict_teacher_patronymic_for_teacher[message.from_user.id] = teacher_patronymic  # вносим отчество в словарь
    # reg_list_for_teacher[teacher_surname,teacher_name,teacher_patronymic]

    teacher_surname = str(dict_surname_teacher_for_teacher.get(message.chat.id)).title()
    # получаем фамилию преподавателя из словаря, с заглавной буквы
    teacher_name = str(dict_name_teacher_for_teacher.get(message.chat.id)).title()
    # получаем имя преподавателя из словаря, с заглавной буквы
    teacher_patronymic = str(dict_teacher_patronymic_for_teacher.get(message.chat.id)).title()
    # получаем отчество преподавателя из словаря, с заглавной буквы
    mes = f"Вы успешно зарегистрированы! \n" \
          f"Ваша фамилия: {teacher_surname.title()} \n" \
          f"Ваше имя: {teacher_name.title()} \n" \
          f"Ваше отчество: {teacher_patronymic.title()} \n"
    # формируем текст сообщения пользователю с его данными
    reg_dict_message_to_edit[message.chat.id] = bot.send_message(message.chat.id,
                                                                 "Проверьте данные на корректность\n❗" + mes +
                                                                 "После завершения процесса регистрации " +
                                                                 "данные изменить невозможно",
                                                                 reply_markup=weather_key(d))

    if not BotDB.teacher_exists(message.from_user.id):  # если преподавателя нет в БД
        try:
            teacher_surname = str(dict_surname_teacher_for_teacher.get(message.from_user.id))
            # получаем фамилию преподавателя из словаря
            teacher_name = str(dict_name_teacher_for_teacher.get(message.from_user.id))
            # получаем имя преподавателя из словаря
            teacher_patronymic = str(dict_teacher_patronymic_for_teacher.get(message.from_user.id))
            # получаем отчество преподавателя из словаря
            BotDB.add_teacher(message.from_user.id, teacher_surname,
                              teacher_name, teacher_patronymic)  # вносим данные преподавателя в БД
        except Exception as e:
            bot.send_message(message.chat.id, "Что-то пошло не так :(")
            error_string = "Ошибка registration.py --->add_teacher_patronymic: " + str(e)
            logFile.log_err(message, error_string)
    else:
        bot.send_message(message.chat.id,
                         "Вы уже зарегистрированы")  # отправка сообщения в случае, если пользователь уже есть в БД


# ------------------------------------------- ОБРАБОТКА КНОПОК -------------------------------------------


@bot.callback_query_handler(func=lambda call: True)  # перехватывает нажатие на кнопку
def completion_registration(call):
    """Функция обработки кнопок при регистрации"""
    data = call.data  # получаем данные нажатой кнопкой
    bot.answer_callback_query(call.id)
    if call.data == "завершить":  # выполняем завершение регистрации
        message_to_edit = reg_dict_message_to_edit.get(call.message.chat.id)
        # получаем из словаря сообщение для редактирования
        name_user = str(dict_name_user_for_users.get(call.message.chat.id)).title()  # получаем из словаря имя
        surname_user = str(dict_surname_user_for_users.get(call.message.chat.id)).title()  # получаем из словаря фамилию
        group_user = str(dict_group_user_for_users.get(call.message.chat.id))  # получаем из словаря группу
        mes = f"Вы успешно зарегистрированы! \n" \
              f"Ваше имя: {name_user.title()} \n" \
              f"Ваша фамилия: {surname_user.title()} \n" \
              f"Ваша группа: {group_user.title()}"
        # формируем текст сообщения пользователю с его данными
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=message_to_edit.message_id, text=mes)  # изменяем сообщение на данные юзера
        bot.send_message(call.message.chat.id, "Для ознакомления с основными функциями бота введите\n/help")
        # отправка вспомогательного сообщения пользователю

        del dict_surname_user_for_users[call.message.chat.id]
        del dict_name_user_for_users[call.message.chat.id]
        del dict_group_user_for_users[call.message.chat.id]
        del reg_dict_message_to_edit[call.message.chat.id]
        # очистка словарей после окончания регистрации

    elif call.data == "изменить":
        message_to_edit = reg_dict_message_to_edit.get(call.message.chat.id)
        # получаем из словаря сообщение для редактирования
        d = {"Имя": "имя", "Фамилию": "фамилия",
             "Группу": "группа", "Завершить изменения": "стоп"}  # словарь с текстом кнопок клавиатуры
        reg_dict_message_to_edit[call.message.chat.id] = bot.edit_message_text(chat_id=call.message.chat.id,
                                                                               message_id=message_to_edit.message_id,
                                                                               text="Что бы вы хотели изменить?",
                                                                               reply_markup=weather_key(d),
                                                                               parse_mode='Markdown')
        # отправка пользователю сообщения с предложением изменений, в которое встроена клавиатура
    elif data == "имя":  # пользователь выбрал изменить имя
        message_to_edit = reg_dict_message_to_edit.get(call.message.chat.id)  # получение сообщения для изменения
        bot.delete_message(call.message.chat.id, message_to_edit.message_id)
        # удаляем сообщение с предложением об изменениями
        msg = bot.send_message(call.message.chat.id,
                               "Введите новое имя")  # отправляем пользователю сообщение с просьбой ввести имя
        bot.register_next_step_handler(msg,
                                       check_name)  # ждём смс, передаём его в check_name
    elif data == "фамилия":  # пользователь выбрал изменить фамилию
        message_to_edit = reg_dict_message_to_edit.get(call.message.chat.id)
        # получаем сообщение для изменения из словаря
        bot.delete_message(call.message.chat.id, message_to_edit.message_id)
        # удаляем сообщение с предложением изменений
        msg = bot.send_message(call.message.chat.id,
                               "Введите новую фамилию")
        # просим пользователя ввести новую фамилию
        bot.register_next_step_handler(msg,
                                       check_surname)  # ждём сообщения пользователя, передаём его в check_surname
    elif data == "группа":  # пользователь выбрал изменить группу
        message_to_edit = reg_dict_message_to_edit.get(call.message.chat.id)
        # получаем сообщение для изменения из словаря
        bot.delete_message(call.message.chat.id, message_to_edit.message_id)
        # удаляем сообщение для изменения по его id
        msg = bot.send_message(call.message.chat.id,
                               "Введите новую группу")
        # просим пользователя ввести новую группу
        bot.register_next_step_handler(msg,
                                       up_group_user)  # ждём сообщения пользователя, передаём его в up_group_user
    elif data == "стоп":  # пользователь выбрал завершить изменения
        message_to_edit = reg_dict_message_to_edit.get(call.message.chat.id)
        # получаем сообщение для изменения из словаря
        reg_dict_message_to_edit[call.message.chat.id] = bot.edit_message_text(chat_id=call.message.chat.id,
                                                                               message_id=message_to_edit.message_id,
                                                                               text="Изменения завершены")
        # изменяем сообщение с предложением изменений на их завершение
        bot.send_message(call.message.chat.id,
                         "Для ознакомления с основными функциями бота введите\n/help")
        # отправка вспомогательного сообщения пользователю
        if BotDB.user_exists(call.message.chat.id):
            del dict_surname_user_for_users[call.message.chat.id]
            del dict_name_user_for_users[call.message.chat.id]
            del dict_group_user_for_users[call.message.chat.id]
            # очистка словарей для пользователя после окончания изменений
        elif BotDB.teacher_exists(call.message.chat.id):
            del dict_surname_teacher_for_teacher[call.message.chat.id]
            del dict_name_teacher_for_teacher[call.message.chat.id]
            del dict_teacher_patronymic_for_teacher[call.message.chat.id]
        del reg_dict_message_to_edit[call.message.chat.id]
        # очистка словарей для преподавателя после окончания изменений

    elif call.data == "п_завершить":  # преподаватель выбрал завершить изменения
        message_to_edit = reg_dict_message_to_edit.get(call.message.chat.id)
        # получаем сообщение для изменения из словаря
        teacher_surname = str(dict_surname_teacher_for_teacher.get(call.message.chat.id))  # получаем из словаря фамилию
        teacher_name = str(dict_name_teacher_for_teacher.get(call.message.chat.id))  # получаем из словаря имя
        teacher_patronymic = str(dict_teacher_patronymic_for_teacher.get(call.message.chat.id))
        # получаем из словаря отчество
        mes = f"Вы успешно зарегистрированы! \n" \
              f"Ваша фамилия: {teacher_surname.title()} \n" \
              f"Ваше имя: {teacher_name.title()} \n" \
              f"Ваше отчество: {teacher_patronymic.title()}"
        # формируем текст сообщения преподавателю с его данными
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=message_to_edit.message_id,
                              text=mes)

        bot.send_message(call.message.chat.id, "Для ознакомления с основными функциями бота введите\n/help")
        # отправка вспомогательного сообщения пользователю

        del dict_surname_teacher_for_teacher[call.message.chat.id]
        del dict_name_teacher_for_teacher[call.message.chat.id]
        del dict_teacher_patronymic_for_teacher[call.message.chat.id]
        del reg_dict_message_to_edit[call.message.chat.id]
        # очистка словарей после окончания изменений

    elif call.data == "п_изменить":  # преподаватель выбрал внести изменения
        message_to_edit = reg_dict_message_to_edit.get(call.message.chat.id)
        # получаем сообщение для изменения из словаря
        d = {"Фамилию": "п_фамилия", "Имя": "п_имя", "Отчество": "п_отчество", "Завершить изменения": "стоп"}
        # словарь с текстом кнопок клавиатуры
        reg_dict_message_to_edit[call.message.chat.id] = bot.edit_message_text(chat_id=call.message.chat.id,
                                                                               message_id=message_to_edit.message_id,
                                                                               text="Что бы вы хотели изменить?",
                                                                               reply_markup=weather_key(d),
                                                                               parse_mode='Markdown')
        # отправка преподавателю сообщения с предложением изменений, в которое встроена клавиатура
    elif data == "п_имя":  # преподаватель выбрал изменить имя
        message_to_edit = reg_dict_message_to_edit.get(call.message.chat.id)
        # получаем сообщение для изменения из словаря
        bot.delete_message(call.message.chat.id, message_to_edit.message_id)
        # удаляем сообщение с предложением изменений по его id
        msg = bot.send_message(call.message.chat.id,
                               "Введите новое имя")
        # просим преподавателя ввести новое имя
        bot.register_next_step_handler(msg,
                                       check_teacher_name)
        # ждём сообщения пользователя, передаём его в check_teacher_name

    elif data == "п_фамилия":  # преподаватель выбрал изменить фамилию
        message_to_edit = reg_dict_message_to_edit.get(call.message.chat.id)
        # получаем сообщение для изменения из словаря
        bot.delete_message(call.message.chat.id, message_to_edit.message_id)
        # получаем сообщение для изменения из словаря
        msg = bot.send_message(call.message.chat.id,
                               "Введите новую фамилию")
        # просим преподавателя ввести новую фамилию
        bot.register_next_step_handler(msg,
                                       check_teacher_surname)
        # ждём сообщения пользователя, передаём его в check_teacher_surname

    elif data == "п_отчество":  # преподаватель выбрал изменить отчество
        message_to_edit = reg_dict_message_to_edit.get(call.message.chat.id)
        # получаем сообщение для изменения из словаря
        bot.delete_message(call.message.chat.id, message_to_edit.message_id)
        # удаляем сообщение с предложением изменений
        msg = bot.send_message(call.message.chat.id,
                               "Введите новое отчество")
        # просим преподавателя ввести новое отчество
        bot.register_next_step_handler(msg,
                                       check_teacher_patronymic)
        # ждём сообщения пользователя, передаём его в check_teacher_patronymic

    else:  # если пользователь нажал на кнопку, которая не "принадлежит" регистрации, передаём call в тест
        test.callback_inline(call)  # функция обработки кнопок теста


def register_handlers_reg(bot):
    bot.message_handler(content_types=['text'])(get_user_text)
