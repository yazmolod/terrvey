#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3
import re
from itertools import chain


class DBController:
    """docstring for DBController"""

    def __init__(self, project):
        self.PROJECT = project
        self.path = self.PROJECT['DATABASE_PATH']
        self.connection = sqlite3.connect(self.path, timeout=15)
        self.cursor = self.connection.cursor()
        # Foreign keys не работают с on delete cascade
        # Поэтому после каждого коннекта к база нужно прописывать это
        # подробнее https://stackoverflow.com/questions/4477269/how-to-make-on-delete-cascade-work-in-sqlite-3-7-4
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.quest_table_names = []
        for i in self.PROJECT['STRUCTURE']:
            table_name = i.get('table_name', None)
            if 'Quest' in table_name:
                self.quest_table_names.append(table_name)
        self.create_default_tables()
        self.create_quest_tables()
        self.create_views()

    def create_default_tables(self):
        '''Создаем таблицы, которые должны быть вне зависимости от конфига'''
        # Таблица с респондентами
        statements = []
        statements.append("""
        CREATE TABLE IF NOT EXISTS 'Respondents' (
        'RespondentId' INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT CHECK('RespondentId'>0),
        'Source' TEXT NOT NULL,
        'District' TEXT,
        'Address' TEXT,
        'Gender' TEXT,
        'Age' INTEGER)""")
        # FOREIGN KEY('AddressId') REFERENCES 'Places'('PlaceId') ON UPDATE CASCADE ON DELETE SET NULL
        #)
        #""")
        # Таблица с местами. Фича не реализована, но идея витает уже третий опрос подряд
        # statements.append("""
        # CREATE TABLE IF NOT EXISTS 'Places' (
        # 'PlaceId' INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        # 'District' TEXT,
        # 'Address' TEXT,
        # 'Name' TEXT,
        # 'Longitude' REAL,
        # 'Latitude' REAL,
        # 'Category' TEXT
        # )
        # """)
        for statement in statements:
            self.cursor.execute(statement)
        self.hard_commit()

    def create_quest_tables(self):
        """Создает в БД таблицы для каждого вопроса на основе файла-конфига"""
        statements = []
        for i in self.PROJECT['STRUCTURE']:
            name = i['table_name']
            qtype = i['type']
            if 'Quest' in name:
                if qtype == 'matrix' or qtype == 'mmatrix':
                    columns = ['AnswerText_%02d' %
                               (j + 1) for j in range(len(i['answer_options']))]
                    columns_text = ' TEXT,\n'.join(columns) + ' TEXT,'
                    msg = """
                    CREATE TABLE IF NOT EXISTS '{}' (
                    'AnswerId' INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    'RespondentId' INTEGER,
                    {}
                    FOREIGN KEY('RespondentId') REFERENCES 'Respondents'('RespondentId') ON UPDATE CASCADE ON DELETE CASCADE)
                    """.format(i['table_name'], columns_text)
                elif qtype == 'opt+' or qtype == 'mopt+':
                    msg = """
                    CREATE TABLE IF NOT EXISTS '{}' (
                    'AnswerId' INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    'RespondentId' INTEGER,
                    'AnswerText' TEXT,
                    'AnotherFlag' INTEGER,
                    FOREIGN KEY('RespondentId') REFERENCES 'Respondents'('RespondentId') ON UPDATE CASCADE ON DELETE CASCADE)
                    """.format(i['table_name'])
                else:
                    msg = """
                    CREATE TABLE IF NOT EXISTS '{}' (
                    'AnswerId' INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    'RespondentId' INTEGER,
                    'AnswerText' TEXT,
                    FOREIGN KEY('RespondentId') REFERENCES 'Respondents'('RespondentId') ON UPDATE CASCADE ON DELETE CASCADE)
                    """.format(i['table_name'])
                statements.append(msg)
        for statement in statements:
            self.cursor.execute(statement)
        self.hard_commit()

    def create_views(self):
        statements = []
        age_borders = (20, 30, 40, 50, 60)
        for i in self.PROJECT['STRUCTURE']:
            name = i['table_name']
            answers = i['answers']
            answer_options = i['answer_options']
            qtype = i['type']
            msg = 'CREATE VIEW IF NOT EXISTS "view_{}" AS '.format(name)
            if 'Quest' in name:
                if qtype == 'matrix' or qtype == 'mmatrix':
                    cols = len(answer_options)
                    count_part = ', '.join(
                        ['COUNT (AnswerText_{:02d})'.format(col + 1) for col in range(cols)])
                    selects = ['SELECT "{0}", {2} FROM "{1}" WHERE "AnswerText_{3}"="{0}"'.format(
                        a, name, count_part, '{:02d}'.format(col + 1))
                        for a in answers for col in range(cols)]
                elif 'opt' in qtype:
                    selects = ['SELECT "{0}", COUNT("AnswerText") FROM "{1}" WHERE "AnswerText"="{0}"'.format(
                        a, name) for a in answers]
                    if '+' in qtype:
                        selects.append(
                            'SELECT "другое, в том числе:", count(AnswerText) FROM "{}" WHERE "AnotherFlag"=1'.format(name))
                        selects.append(
                            'SELECT AnswerText, count(AnswerText) FROM "{}" WHERE "AnotherFlag"=1 GROUP BY AnswerText'.format(name))
                else:
                    selects = ['SELECT RespondentId, AnswerText FROM "{}"'.format(name)]
            elif 'Respondents' == name:
                selects = []
                selects.append('SELECT "Всего опрошенных", count (RespondentId) FROM Respondents')
                selects.append('SELECT null, null')
                selects.append('SELECT "Источник", null')
                selects.append('SELECT Source, count (Source) FROM Respondents GROUP BY Source')
                selects.append('SELECT null, null')
                selects.append('SELECT "Пол", null')
                selects.append('SELECT Gender, count (Gender) FROM Respondents GROUP BY Gender')
                selects.append('SELECT null, null')
                selects.append('SELECT "Район", null')
                selects.append('SELECT District, count (District) FROM Respondents GROUP BY District')
                selects.append('SELECT null, null')
                selects.append('SELECT "Возраст", null')
                low_border = 1
                for age in age_borders:
                    selects.append('SELECT "{0}-{1}", count (age) FROM Respondents WHERE age BETWEEN {0} and {1}'.format(low_border, age))
                    low_border = age+1
                selects.append('SELECT ">{0}", count (age) FROM Respondents WHERE age > {0}'.format(age))
                selects.append('SELECT "Неизвестно", count (age) FROM Respondents WHERE age = 0'.format(age))

            msg += '\nUNION ALL\n'.join(selects)
            statements.append(msg)
        for statement in statements:
            try:
                self.cursor.execute(statement)
            except:
                print (statement)
                raise Exception
        self.hard_commit()

    def set_values(self, values, commit=True, delete_existing=True):
        current_resp = values['Respondents']['RespondentId']
        if current_resp in self.get_all_resp_id() and delete_existing:
            # Если данный респондент уже есть в базе - удаляем его
            self.delete_resp(current_resp)
        # Если данный респондент отсутствует в базе - добавляем его и все данные
        self.add_new_resp(values['Respondents'])
        statements = []
        for table_name in values:
            if table_name != 'Respondents':
                table_values = values[table_name]
                for i in range(len(table_values)):
                    if not table_values[i] and type(table_values[i]) is not list:
                        continue
                    # определяем тип вопроса по типу ответа
                    # в соответствии с заранее продуманной схемой формата передачи результатов
                    #
                    # в value меняем кавычки на двойные кавычки чтобы избежать ошибок
                    # при Insert
                    #
                        # матрица
                    if type(table_values[i]) is list:
                        column_name = 'AnswerText_%02d' % (i + 1)
                        for j in table_values[i]:
                            value = j.replace('"', '""')
                            statements.append('''INSERT INTO "{}" (RespondentId, {}) 
                                                                    VALUES ({}, "{}")'''.format(table_name, column_name, current_resp, value))
                        # opt+ или mopt+
                    elif type(table_values[i]) is tuple:
                        value = table_values[i][0]
                        value = value.replace('"', '""')
                        flag = table_values[i][1]
                        statements.append('''INSERT INTO "{}" (RespondentId, AnswerText, AnotherFlag)
                                            VALUES ({}, "{}", {})'''.format(table_name, current_resp, value, flag))
                    else:
                        value = table_values[i]
                        value = value.replace('"', '""')
                        statements.append('''INSERT INTO "{}" (RespondentId, AnswerText) VALUES ({}, "{}")'''.format(
                            table_name, current_resp, value))
        for statement in statements:
            self.cursor.execute(statement)
        if commit:
            self.hard_commit()

    def get_values(self, current_resp):
        '''Предоставляет данные для GUI'''
        result_values = {}
        respondent_columns = self.get_column_names('Respondents')
        self.cursor.execute("""
            SELECT *
            FROM Respondents
            WHERE RespondentId = {}""".format(current_resp))
        respondent_values = self.cursor.fetchall()[0]
        result_values['Respondents'] = {
            respondent_columns[i]: respondent_values[i] for i in range(len(respondent_columns))}
        for table_name in self.quest_table_names:
            if self.PROJECT['TYPES'][table_name] in ('matrix', 'mmatrix'):
                result_values[table_name] = [[] for i in range(
                    self.PROJECT['MATRIX_WIDTH'][table_name])]
            else:
                result_values[table_name] = []
            self.cursor.execute(
                'SELECT * FROM "{}" WHERE RespondentId = {}'.format(table_name, current_resp))
            table_values = self.cursor.fetchall()
            for table_value in table_values:
                # пропускаем AnsId и RespId
                value = table_value[2:]
                if self.PROJECT['TYPES'][table_name] in ('opt+', 'mopt+'):
                    result_values[table_name].append(value)
                elif self.PROJECT['TYPES'][table_name] in ('matrix', 'mmatrix'):
                    for i in range(len(value)):
                        if value[i]:
                            result_values[table_name][i].append(value[i])
                else:
                    result_values[table_name].append(value[0])
        return result_values

    def add_empty_resp(self):
        new_resp_id = self.get_last_resp_id() + 1
        self.cursor.execute("""
            INSERT INTO Respondents (RespondentId, Source)
            VALUES ({}, 'Бумага')
            """.format(new_resp_id))
        self.hard_commit()

    def add_new_resp(self, resp_values):
        self.cursor.execute("""
            INSERT INTO 'Respondents' (RespondentId, Source, District, Address, Gender, Age)
            VALUES (:resp, :source, :district, :address, :gender, :age)
            """, {
            'resp': resp_values['RespondentId'],
            'source': resp_values.get('Source', ''),
            'district': resp_values.get('District', ''),
            'address': resp_values.get('Address', ''),
            'gender': resp_values.get('Gender', ''),
            'age': resp_values.get('Age', 0),
        })
        self.hard_commit()

    def get_all_items(self, table_name, col_name):
        self.cursor.execute("SELECT %s FROM %s" % (col_name, table_name))
        return [i[0] for i in self.cursor.fetchall()]

    def fast_select(self, select_column, select_table, where_column, where_value):
        # удобный поиск id для другой таблицы. Например, если нужен PlaceId по его координатам
        statement = ("""
            SELECT 
            {}
            FROM
            {}
            WHERE ({} = '{}')
            """.format(select_column, select_table, where_column, where_value))
        self.cursor.execute(statement)
        return self.cursor.fetchall()[0][0]

    def get_column_names(self, table_name):
        self.cursor.execute("PRAGMA table_info (" + table_name + ")")
        return [i[1] for i in self.cursor.fetchall()]

    def get_resp_count(self):
        self.cursor.execute("""
            SELECT
                count(*)
            FROM
                Respondents
            """)
        return self.cursor.fetchall()[0][0]

    def get_last_resp_id(self):
        self.cursor.execute("""
            SELECT
                max(RespondentId)
            FROM
                Respondents
            """)
        return self.cursor.fetchall()[0][0]

    def get_all_resp_id(self):
        self.cursor.execute("""
            SELECT
                RespondentId
            FROM
                Respondents
            ORDER BY RespondentId
            """)
        result = [i[0] for i in self.cursor.fetchall()]
        return result

    def hard_commit(self):
        '''Подтверждение транзакции в базу данных с обработкой ошибок'''
        # try:
        self.connection.commit()
        self.cursor.execute("PRAGMA foreign_keys = ON")
        # except sqlite3.DatabaseError as e:
        #   print(e)

    def delete_resp(self, resp_id):
        self.cursor.execute(
            'DELETE FROM Respondents WHERE RespondentId = %d' % (resp_id))
        self.hard_commit()

    def is_empty_table(self, table_name):
        self.cursor.execute("SELECT count(*) FROM %s" % (table_name))
        if self.cursor.fetchall()[0][0] == 0:
            return True
        else:
            return False


if __name__ == '__main__':
    controller = DBController('test.sqlite3')
    val = {'Quest_03': [('занимаюсь спортом', 0), ('просто гуляю, наслаждаюсь общением с природой', 0), ('летом загораю, плаваю, купаюсь', 0), ('зимой катаюсь на лыжах, санках', 0), ('катаюсь на лошадях', 0), ('обычно пользуюсь аттракционами', 0), ('люблю посидеть в кафе на свежем воздухе', 0), ('работаю, читаю книгу', 0), ('устраиваю пикники, праздники', 0), ('собираю травы, цветы, желуди', 0), ('встречаюсь с друзьями', 0), ('назначаю свидания', 0)], 'Quest_04': [('здесь удобно заниматься спортом', 0), ('это тихое место, где можно отдохнуть от городской суеты', 0), ('здесь чистый воздух', 0), ('больше всего мне нравится его природная основа', 0), ('возможность отдохнуть здесь семьей', 0), ('парк - прекрасное место для прогулок с детьми', 0), ('возможность просто пообщаться с природой, спуститься к Волге', 0), ('за то, что здесь есть пляжная зона', 0)], 'Quest_comment': ['Очень боюсь, что из загородного парка сделают парк типа гагарина. Необходимо сохранить как можно больше зелени и лесопосадки, не нужно "закатывать" все в асфальт и строить многофункциональные зоны. Ценность этого парка в его природе. Очевидно, что ему необходима реконструкция, но она должна заключаться в большей организованности парка, чтобы лесу было комфортно расти, а посетителям - наслаждаться им'], 'Quest_05': [
        'парк не случайно называется загородным, значит, он должен отличаться от других парков города обилием природных элементов, продуманным благоустройством, видовыми площадками, декоративными растениями, фонтанами, летними кафе; это - экологическая ниша большого города'], 'Quest_07': [('подъемом пешеходных дорожек над уровнем земли', 0), ('организацией видовых площадок', 0), ('максимальным сохранением природы, подсадкой новых деревьев', 0), ('обогащением парковой территории новыми функциями', 0)], 'Quest_02': ['с семьей'], 'Quest_01': ['практически каждый день'], 'Quest_06': ['Проект 2'], 'Quest_08': ['Фрагмент 1 - многоуровневая трасса пешеходного движения', 'Фрагмент 3 - использование рельефа для размещения современного объекта при сохранении объекта культурного наследия', 'Фрагмент 8 - организация спуска к Волге: многоярусная лестница с элементами озеленения, дополненная вертикальным подъемником и видовой площадкой', 'Фрагмент 10 - размещение в парке теплиц и открытого кинотеатра', 'Фрагмент 13 - пляжная зона с понтонными выходами на воду, организация конного двора, устройство фуникулера со станцией в виде 3d деревьев', 'Фрагмент 14 - видовая площадка в виде палубы корабля и устройством места для загара', 'Фрагмент 16 - вариант подачи проекта', 'Фрагмент 19 - многоуровневая организация прибрежной территории', 'Фрагмент 20 - пешеходная дорожка с игровыми элементами'], 'Respondents': {'RespondentId': 163, 'District': 'Октябрьский', 'Address': '6 радиальная, дом 7', 'Source': 'Онлайн', 'Gender': 'женский', 'Age': '25'}}
    controller.set_values(val)
