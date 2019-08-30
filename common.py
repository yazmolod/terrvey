JSON_PATH = "2rd stage\schema.json"
DEFAULT_VALUES = {
    "Districts": [
        "Неизвестно",
        "Самарский",
        "Ленинский",
        "Октябрьский",
        "Железнодорожный",
        "Советский",
        "Промышленный",
        "Кировский",
        "Красноглинский",
        "Куйбышевский"

    ],

    "Genders": [
        "Неизвестно",
        "Мужской",
        "Женский"
    ],

    "Sources": [
        "Бумага",
        "Онлайн"
    ]
}

# СХЕМА ПЕРЕДАЧИ ДАННЫХ
# Таблицы с вопросами:#
# матрицы - [[],[],[]] где во вложенных списках содержатся строки конкретного стоблца
# опции с вариантом "другое" - [(),(),()], где в кортежах содержится ответ и флаг другого ответа (0 или 1)
# все остальное - [, , ,], где просто перечисляются разные ответы

# Данные по респондентам:
# Заносятся в соответствующую базе данных графу без каких-то либо вложений
# НазваниеТаблицы>Столбец: [,,,]

# Пример данных:

# Респонденты
# opt - один из списка
# opt+ - один из списка с вариантом ДРУГОЕ
# mopt - несколько из списка
# mopt+ - несколько из списка с вариантом ДРУГОЕ
# text - текст в одну строку
# mtext - текст в несколько строк
# matrix - матрица с одним выбором в ряд
# mmatrix - матрица с несколькими выборами в ряд

# {
# 'Respondents': {'RespondentId': 3, 'Age': [''], 'Gender': ['']},
# 'Quest_01': ['Вариант 4'],
# 'Quest_02': [('asd', 1)],
# 'Quest_03': ['Вариант 3', 'Вариант 5'],
# 'Quest_04': [('Вариант 2', 0), ('asdas', 1)],
# 'Quest_05': ['adada'],
# 'Quest_06': ['Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aliquam ac diam orci. Aenean placerat j']
# 'Quest_07': [['Ряд 5'], [], []],
# 'Quest_08': [[], ['Ряд 3']]
# }


import json
import sys
import traceback

with open(JSON_PATH, encoding='utf-8') as json_file:
    JSON = json.load(json_file)
TYPES = {i['table_name']: i['type'] for i in JSON}
MATRIX_WIDTH = {i['table_name']: len(
    i['answer_options']) for i in JSON if 'answer_options' in i}


def get_JSON_item_by_attribute(**kwargs):
    res = []
    for k, v in kwargs.items():
        for i in JSON:
            if i.get(k, None) == v:
                res.append(i)
                break
    if len(res) == 1:
        return res[0]
    else:
        res


def debugger(func):
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            del exc_info
    return wrapper
