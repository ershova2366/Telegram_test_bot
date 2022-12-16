import datetime

"ФАЙЛ ДЛЯ ЗАПИСИ действий пользователей в txt (telegram --> .txt)"


def log(message):  # def log - запись сообщений от пользователя

    dt = datetime.datetime.now()
    try:
        s = (" Сообщение от {0} {1} (id = {2}) СООБЩЕНИЕ: {3}".format(message.from_user.first_name,
                                                                      message.from_user.last_name,
                                                                      str(message.from_user.id), message.text))
        file = open("log.txt", 'a', encoding='utf-8')
        file.write(str(dt) + str(s) + "\n")
        file.close()
    except Exception as e:
        print(e)


def log_err(message="none", err="none"):  # def log_err - запсиь ощибок при обработки try

    dt = datetime.datetime.now()
    try:
        s = (" Сообщение от id = {0} СООБЩЕНИЕ: {1}".format(str(message.from_user.id), message.text))
    except Exception as e:
        s = " Полученные данные: " + str(message)

    try:
        file = open("log_err.txt", 'a', encoding='utf-8')
        file.write("----------------------------" + "\n")
        file.write(str(dt) + str(s) + "\n")
        file.write(str(err) + "\n")
        file.write("----------------------------" + "\n")
        file.close()

        print("----------------------------" + "\n")
        print(str(dt) + str(s) + "\n")
        print(str(err) + "\n")

    except Exception as e:
        print(e)
