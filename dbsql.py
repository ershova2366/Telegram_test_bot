import sqlite3
import logFile

"ФАЙЛ ДЛЯ ОБРАБОТКИ SQL запросов (program <--> DB)"


class BotDB:

    def __init__(self, db_file):
        try:
            self.conn = sqlite3.connect(db_file, check_same_thread=False)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            error_string = "Ошибка dbsql.py --->__init__: " + str(e)
            logFile.log_err(err=error_string)

    def user_exists(self, telegram_id):
        """Функция проверки наличия юзера в базе"""
        try:
            result = self.cursor.execute("SELECT `telegram_id` FROM `users` WHERE `telegram_id` = ?", (telegram_id,))
            return bool(len(result.fetchall()))
        except sqlite3.Error as e:
            error_string = "Ошибка dbsql.py --->user_exists: " + str(e)
            logFile.log_err(err=error_string)

    def add_user(self, telegram_id, name_user, surname_user, group_user):
        """Функция добавления юзера в базу"""
        try:
            self.cursor.execute(
                """INSERT INTO `users` ('telegram_id','name_user','surname_user','group_user') 
                   VALUES (?,?,?,?)""",
                (telegram_id, name_user.title(), surname_user.title(), group_user))
            return self.conn.commit()
        except sqlite3.Error as e:
            error_string = "Ошибка dbsql.py --->add_user: " + str(e)
            logFile.log_err(err=error_string)

    def teacher_exists(self, telegram_id):
        """Функция проверки наличия преподавателя в базе"""
        try:
            result = self.cursor.execute("SELECT `telegram_id` FROM `teacher` WHERE `telegram_id` = ?", (telegram_id,))
            return bool(len(result.fetchall()))
        except sqlite3.Error as e:
            error_string = "Ошибка dbsql.py --->teacher_exists: " + str(e)
            logFile.log_err(err=error_string)

    def add_teacher(self, telegram_id, surname_teacher, name_teacher, patronymic_teacher):
        """Функция внесения преподавателя в базу"""
        try:
            self.cursor.execute(
                """INSERT INTO `teacher` ('telegram_id','surname_teacher','name_teacher','patronymic_teacher') 
               VALUES (?,?,?,?)""",
                (telegram_id, surname_teacher.title(), name_teacher.title(), patronymic_teacher.title()))
            return self.conn.commit()
        except sqlite3.Error as e:
            error_string = "Ошибка dbsql.py --->add_teacher: " + str(e)
            logFile.log_err(err=error_string)

    def get_teacher(self, telegram_id):
        """Функция возвращает информацию о преподавателе"""
        try:
            result = self.cursor.execute("SELECT * FROM `teacher` WHERE `telegram_id` = ?", (telegram_id,))
            return result.fetchall()
        except sqlite3.Error as e:
            error_string = "Ошибка dbsql.py --->get_teacher: " + str(e)
            logFile.log_err(err=error_string)

    def get_user(self, telegram_id):
        """Функция возвращает информацию о пользователе"""
        try:
            result = self.cursor.execute("SELECT * FROM `users` WHERE `telegram_id` = ?", (telegram_id,))
            return result.fetchall()
        except sqlite3.Error as e:
            error_string = "Ошибка dbsql.py --->get_user: " + str(e)
            logFile.log_err(err=error_string)

    def drop_test(self, name_table, id_question):
        """Функция возвращает вопрос и таблицы name_table и записывает в БД информацию о прохождении ученика"""
        try:
            result = self.cursor.execute(
                f"""SELECT `questions`,`answerA`,`answerB`,`answerC`,`answerD`,`true_answer`
                 FROM {name_table} 
                 WHERE `id_question`=?""", (id_question,))
            return result.fetchall()
        except sqlite3.Error as e:
            error_string = "Ошибка dbsql.py --->drop_test: " + str(e)
            logFile.log_err(err=error_string)

    def max_question_number(self, name_table):
        """Функция возвращает максимальное число вопросов"""
        try:
            result = self.cursor.execute(f"SELECT MAX(id_question) FROM {name_table}")
            return result.fetchone()
        except sqlite3.Error as e:
            error_string = "Ошибка dbsql.py --->max_question_number: " + str(e)
            logFile.log_err(err=error_string)

    def user_answer(self, answer, id_question, name_table):
        """Достаем ответ пользователя в виде строки"""
        try:
            result = self.cursor.execute(f"SELECT {answer} FROM {name_table} WHERE `id_question`=?", (id_question,))
            return result.fetchone()
        except sqlite3.Error as e:
            error_string = "Ошибка dbsql.py --->user_answer: " + str(e)
            logFile.log_err(err=error_string)

    def check_test_in_db(self, name_table):
        """Проверка на наличие таблицы в бд"""
        try:
            result = self.cursor.execute(f"SELECT name FROM sqlite_sequence WHERE name='{name_table}' ")
            return bool(len(result.fetchall()))
        except sqlite3.Error as e:
            error_string = "Ошибка dbsql.py --->check_test_in_db: " + str(e)
            logFile.log_err(err=error_string)

    def create_test(self, name_table, telegram_id):
        """Функция создаёт новую таблицу из excel файла пользователя"""
        score_name_table = name_table + "_score"
        self.cursor.execute(f"""CREATE TABLE IF NOT EXISTS '{name_table}' 
                                ('id_question' INTEGER, 'questions' TEXT NOT NULL,
                                 'answerA' TEXT,
                                  'answerB' TEXT,
                                  'answerC' TEXT,
                                  'answerD' TEXT,
                                  'true_answer' TEXT NOT NULL,
                                  PRIMARY KEY("id_question" AUTOINCREMENT));""")

        self.cursor.execute(f"""CREATE TABLE {score_name_table} ("score_id"	INTEGER NOT NULL,
                                                                 "telegram_id" INTEGER NOT NULL,
                                                                 "score" INTEGER NOT NULL,
                                                                  PRIMARY KEY("score_id" AUTOINCREMENT));""")

        self.cursor.execute("INSERT INTO 'table_techer'('telegram_id','name_table') VALUES(?,?)",
                            (telegram_id, name_table))
        return self.conn.commit()

    def insert_new_test(self, name_file_s, length, worksheet):
        """Заполнение нового теста"""
        for i in range(3, length + 1):
            if worksheet != "" or worksheet != " ":
                questions = worksheet[i][0].value
                answerA = worksheet[i][1].value
                answerB = worksheet[i][2].value
                answerC = worksheet[i][3].value
                answerD = worksheet[i][4].value
                true_answer = worksheet[i][5].value
                self.cursor.execute(
                    f"""INSERT INTO '{name_file_s[0]}'
                     (`questions`,`answerA`,`answerB`,`answerC`,`answerD`,`true_answer`)
                     VALUES (?,?,?,?,?,?)""",
                    (questions, answerA, answerB, answerC, answerD, true_answer))

        return self.conn.commit()

    def insert_score_test(self, name_file, telegram_id, balls, ):
        """Заполнение таблицы с оценками учеников"""
        try:
            score_name_table = name_file + "_score"
            self.cursor.execute(
                f"INSERT INTO '{score_name_table}' (`telegram_id`,`score`) VALUES (?,?)", (telegram_id, balls))
            return self.conn.commit()
        except sqlite3.Error as e:
            error_string = "Ошибка dbsql.py --->insert_score_test: " + str(e)
            logFile.log_err(err=error_string)

    def drop_score_from_table(self, name_file):
        try:
            self.cursor.execute(f"SELECT * FROM {name_file}")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            error_string = "Ошибка dbsql.py --->drop_score_from_table: " + str(e)
            logFile.log_err(err=error_string)

    def delete_test(self, name_table):
        """Удаление теста"""
        score_name_table = name_table + "_score"
        self.cursor.execute(f"DROP TABLE '{name_table}';")
        self.cursor.execute(f"DROP TABLE '{score_name_table}';")
        self.cursor.execute(f"DELETE FROM 'table_techer' WHERE name_table='{name_table}'")

        return self.conn.commit()

    def drop_score_for_user(self, name_table, telegram_id):
        """Функция вывода личной оценки ученика"""
        try:
            score_name_table = name_table + "_score"
            self.cursor.execute(f"""  SELECT score
                                      FROM {score_name_table} 
                                      WHERE telegram_id={telegram_id}""")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            error_string = "Ошибка dbsql.py --->drop_score_for_user: " + str(e)
            logFile.log_err(err=error_string)

    def drop_score_for_teacher(self, name_table):
        """Функция вывода всех оценок за тест"""
        try:
            score_name_table = name_table + "_score"
            self.cursor.execute(f"""SELECT users.surname_user, users.name_user,  
                                    users.group_user, {score_name_table}.score
                                    FROM users, {score_name_table}
                                    WHERE  users.telegram_id = {score_name_table}.telegram_id""")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            error_string = "Ошибка dbsql.py --->drop_score_for_teacher: " + str(e)
            logFile.log_err(err=error_string)

    def drop_name_test_for_teacher(self, telegram_id):
        try:
            self.cursor.execute(f"""  SELECT name_table
                                      FROM table_techer
                                      WHERE telegram_id={telegram_id}""")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            error_string = "Ошибка dbsql.py --->drop_name_test_for_teacher: " + str(e)
            logFile.log_err(err=error_string)

    def update_user_name(self, new_name):
        """Функция изменения имени студента"""
        try:
            telegram_id = new_name.from_user.id
            new_name = new_name.text.title()
            self.cursor.execute("UPDATE `users` SET `name_user` = ? WHERE `telegram_id` = ?", (new_name, telegram_id,))
            return self.conn.commit()
        except sqlite3.Error as e:
            error_string = "Ошибка dbsql.py --->update_user_name: " + str(e)
            logFile.log_err(err=error_string)

    def update_user_surname(self, new_surname):
        """Функция изменения фамилии студента"""
        try:
            telegram_id = new_surname.from_user.id
            new_surname = new_surname.text.title()
            self.cursor.execute("""UPDATE `users` 
                                   SET `surname_user` = ? 
                                   WHERE `telegram_id` = ?""", (new_surname, telegram_id,))
            return self.conn.commit()
        except sqlite3.Error as e:
            error_string = "Ошибка dbsql.py --->update_user_surname: " + str(e)
            logFile.log_err(err=error_string)

    def update_user_group(self, new_group):
        """Функция изменения группы студента"""
        try:
            telegram_id = new_group.from_user.id
            new_group = new_group.text
            self.cursor.execute("""UPDATE `users` 
                                   SET `group_user` = ? 
                                   WHERE `telegram_id` = ?""", (new_group, telegram_id,))
            return self.conn.commit()
        except sqlite3.Error as e:
            error_string = "Ошибка dbsql.py --->update_user_group: " + str(e)
            logFile.log_err(err=error_string)

    def update_teacher_name(self, name):
        """Функция изменения имени преподавателя"""
        try:
            telegram_id = name.from_user.id
            name = name.text.title()
            self.cursor.execute("""UPDATE `teacher` 
                                   SET `name_teacher` = ?
                                   WHERE `telegram_id` = ?""", (name, telegram_id,))
            return self.conn.commit()
        except sqlite3.Error as e:
            error_string = "Ошибка dbsql.py --->update_teacher_name: " + str(e)
            logFile.log_err(err=error_string)

    def update_teacher_surname(self, surname):
        """Функция изменения фамилии преподавателя"""
        try:
            telegram_id = surname.from_user.id
            surname = surname.text.title()
            self.cursor.execute("""UPDATE `teacher` 
                                   SET `surname_teacher` = ? 
                                   WHERE `telegram_id` = ?""", (surname, telegram_id,))
            return self.conn.commit()
        except sqlite3.Error as e:
            error_string = "Ошибка dbsql.py --->update_teacher_surname: " + str(e)
            logFile.log_err(err=error_string)

    def update_teacher_patronymic(self, patronymic):
        """Функция изменения отчества преподавателя"""
        try:
            telegram_id = patronymic.from_user.id
            patronymic = patronymic.text.title()
            self.cursor.execute("""UPDATE `teacher`
                                   SET `patronymic_teacher` = ? 
                                   WHERE `telegram_id` = ?""", (patronymic, telegram_id,))
            return self.conn.commit()
        except sqlite3.Error as e:
            error_string = "Ошибка dbsql.py --->update_teacher_patronymic: " + str(e)
            logFile.log_err(err=error_string)
