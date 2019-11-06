import csv


class CSVParser:

    def __init__(self, csv_path, structure):
        with open(csv_path, encoding='utf-8') as f:
            self.csv_row_count = sum(1 for line in f)         
        self.csv_file = open(csv_path, encoding='utf-8')
        self.csv_reader = csv.reader(self.csv_file)
        self.STRUCTURE = structure

    def split_multi_answer(self, answer):
        # если в ответе имеется точка с запятой то будет кирдык
        # моя регулярная магия пока не придумала на это ответ
        answer = answer.replace('; ', '|')
        answer = answer.split(';')
        return [i.replace('|', '; ') for i in answer]

    def parse_row(self, row):
        result = {'Respondents':{'Source':'Онлайн'}}
        for item in self.STRUCTURE:
            # матрицы
            if item['type'] == 'matrix' or item['type'] == 'mmatrix':
                item_result = [[] for j in range(len(item['answer_options']))]
                for i in range(len(item['answers'])):
                    raw_value = row[item['csv_column'] + i]
                    values = self.split_multi_answer(raw_value)
                    for value in values:
                        if value:
                            value_index = item['answer_options'].index(value)
                            item_result[value_index].append(item['answers'][i])
            # вопросы с вариантом другое
            elif item['type'] == 'opt+' or item['type'] == 'mopt+':
                value = row[item['csv_column']]
                values = self.split_multi_answer(value)
                item_result = []
                for value in values:
                    if value in item['answers']:
                        item_result.append((value, 0))
                    else:
                        item_result.append((value, 1))
            # простые и текстовые вопросы
            else:
                value = row[item['csv_column']]
                values = self.split_multi_answer(value)
                item_result = [i for i in values]

            if item['table_name'] == 'Respondents':
                result['Respondents'][item['table_column']] = item_result[0]
            else:
                result[item['table_name']] = item_result
        return result


    def parse_all(self, start_respondentid=1, start_row=1, stop_row=99999, have_header=True):
        line_counter = 1
        for row in self.csv_reader:
            if line_counter < start_row + have_header:
                line_counter += 1 
                continue
            if line_counter > stop_row + have_header:
                break
            row_result = self.parse_row(row)
            row_result['Respondents']['RespondentId'] = start_respondentid
            line_counter += 1
            start_respondentid += 1
            yield row_result

if __name__ == '__main__':
    parser = CSVParser('1 этап/Самара загородный парк_1289.csv')
    a = {'have_header': True, 'start_row': 1, 'start_respondentid': 131}
    counter = 1
    for i in parser.parse_all(**a):
        print (counter)
        counter += 1
