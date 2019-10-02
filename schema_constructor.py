from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
import sys
import json


class SchemaBrick(QWidget):
    def __init__(self):
        super().__init__()
        self.loadUI()

    def loadUI(self):
        self.questionTypes = [
            ('Текст (строка)', 'text'),
            ('Текст (абзац)', 'mtext'),
            ('Один из списка', 'opt'),
            ('Несколько из списка', 'mopt'),
            ('Матрица с одним выбором', 'matrix'),
            ('Матрица с несколькими выборами', 'mmatrix')
        ]
        self.answers = []
        self.columns = []

        self.answersCountSpinBox = QSpinBox(self)
        self.matrixColumnsCountSpinBox = QSpinBox(self)
        self.csvColumnSpinBox = QSpinBox(self)
        self.questionTypeComboBox = QComboBox(self)
        self.questionTitleLineEdit = QLineEdit(self)
        self.tableNameLineEdit = QLineEdit(self)
        self.tableColumnLineEdit = QLineEdit(self)
        self.otherAnswerCheckBox = QCheckBox(self)

        self.layout = QGridLayout()
        self.layout.addWidget(self.questionTypeComboBox, 1, 1)
        self.layout.addWidget(QLabel('Тип вопроса'), 1, 0)
        self.layout.addWidget(self.otherAnswerCheckBox, 2, 1)
        self.layout.addWidget(QLabel('Вариант "другое"'), 2, 0)
        self.layout.addWidget(self.questionTitleLineEdit, 3, 1)
        self.layout.addWidget(QLabel('Заголовок вопроса'), 3, 0)
        self.layout.addWidget(self.tableNameLineEdit, 4, 1)
        self.layout.addWidget(QLabel('Имя таблицы вопроса'), 4, 0)
        self.layout.addWidget(self.tableColumnLineEdit, 5, 1)
        self.layout.addWidget(QLabel('Имя столбца'), 5, 0)
        self.layout.addWidget(self.csvColumnSpinBox, 6, 1)
        self.layout.addWidget(QLabel('Столбец в CSV'), 6, 0)
        self.layout.addWidget(QLabel('Вариант ответа'), 0, 2)
        self.layout.addWidget(QLabel('Столбец ответа'), 0, 3)
        self.layout.addWidget(self.answersCountSpinBox, 1, 2)
        self.layout.addWidget(self.matrixColumnsCountSpinBox, 1, 3)
        self.setLayout(self.layout)

        self.answersCountSpinBox.setMinimum(0)
        self.matrixColumnsCountSpinBox.setMinimum(0)
        self.csvColumnSpinBox.setMinimum(1)
        self.questionTypeComboBox.addItems([i[0] for i in self.questionTypes])
        self.questionTypeComboBox.setCurrentIndex(-1)

        self.questionTypeComboBox.currentIndexChanged.connect(self.typeChanged)
        self.answersCountSpinBox.valueChanged.connect(self.answersChanged)
        self.matrixColumnsCountSpinBox.valueChanged.connect(
            self.columnsChanged)
        self.tableNameLineEdit.textChanged.connect(self.tableNameChanged)

    def tableNameChanged(self, text):
        stackedWidget = self.parent()
        i = stackedWidget.count()-1
        stackedWidget.parent().setTabText(i, text)

    def answersChanged(self, value):
        if value > len(self.answers):
            while len(self.answers) != value:
                le = QLineEdit()
                self.layout.addWidget(le, len(self.answers) + 2, 2)
                self.answers.append(le)
        else:
            while len(self.answers) != value:
                le = self.answers.pop()
                le.deleteLater()

    def columnsChanged(self, value):
        if value > len(self.columns):
            while len(self.columns) != value:
                le = QLineEdit()
                self.layout.addWidget(le, len(self.columns) + 2, 3)
                self.columns.append(le)
        else:
            while len(self.columns) != value:
                le = self.columns.pop()
                le.deleteLater()

    def typeChanged(self, index):
        self.answersCountSpinBox.setValue(0)
        self.matrixColumnsCountSpinBox.setValue(0)
        self.otherAnswerCheckBox.setChecked(False)
        if index <= 1:
            self.answersCountSpinBox.setEnabled(False)
            self.matrixColumnsCountSpinBox.setEnabled(False)
            self.otherAnswerCheckBox.setEnabled(False)
        elif 1 < index < 4:
            self.answersCountSpinBox.setEnabled(True)
            self.matrixColumnsCountSpinBox.setEnabled(False)
            self.otherAnswerCheckBox.setEnabled(True)
        elif 4 <= index:
            self.answersCountSpinBox.setEnabled(True)
            self.matrixColumnsCountSpinBox.setEnabled(True)
            self.otherAnswerCheckBox.setEnabled(False)

    def getValues(self):
        answers = [i.text() for i in self.answers]
        answer_options = [i.text() for i in self.columns]
        quest = self.questionTitleLineEdit.text()
        table_name = self.tableNameLineEdit.text()
        table_column = self.tableColumnLineEdit.text()
        csv_column = int(self.csvColumnSpinBox.text()) - 1
        type_text = self.questionTypes[self.questionTypeComboBox.currentIndex(
        )][1]
        type_bool = self.otherAnswerCheckBox.isChecked()
        if type_bool:
            type_text += '+'
        values = {
            'answers': answers,
            'answer_options': answer_options,
            'quest': quest,
            'table_name': table_name,
            'type': type_text,
            'csv_column': csv_column,
            'table_column': table_column,
        }
        return values

    def setValues(self, values):
        for i in self.questionTypes:
            if i[1]==values['type'].strip('+'):
                current_type = i[0]  
        index = self.questionTypeComboBox.findText(current_type)
        self.questionTypeComboBox.setCurrentIndex(index)
        self.answersCountSpinBox.setValue(len(values['answers']))
        self.matrixColumnsCountSpinBox.setValue(len(values['answer_options']))
        self.csvColumnSpinBox.setValue(values['csv_column'] + 1)
        self.questionTitleLineEdit.setText(values['quest'])
        self.tableNameLineEdit.setText(values['table_name'])
        self.tableColumnLineEdit.setText(values['table_column'])
        self.otherAnswerCheckBox.setChecked('+' in values['type'])
        for iAnswer in range(len(values['answers'])):
            self.answers[iAnswer].setText(values['answers'][iAnswer])
        for iAnswerOption in range(len(values['answer_options'])):
            self.columns[iAnswerOption].setText(values['answer_options'][iAnswerOption])

class SchemaConstructor(QWidget):
    def __init__(self):
        super().__init__()
        loadUi('ui\\SchemaConstructor.ui', self)
        self.initSignals()

    def initSignals(self):
        self.addButton.clicked.connect(self.addQuestion)
        self.removeButton.clicked.connect(self.removeQuestion)
        self.exportButton.clicked.connect(self.exportProject)
        self.importButton.clicked.connect(self.importProject)

    def addQuestion(self):
        wid = SchemaBrick()
        self.tabWidget.addTab(wid, '?')
        return wid

    def removeQuestion(self):
        self.tabWidget.removeTab(self.tabWidget.currentIndex())

    def exportProject(self):
        schema = []
        for i in range(len(self.tabWidget)):
            wid = self.tabWidget.widget(i)
            schema.append(wid.getValues())
        fname = QFileDialog.getSaveFileName(
            self, 'Создать проект опроса', '.', "База данных (*.json)")[0]
        if fname:
            with open(fname, 'w', encoding='utf-8') as file:
                json.dump(schema, file, ensure_ascii=False)

    def importProject(self):
        fname = QFileDialog.getOpenFileName(
            self, 'Открыть проект опроса', '.', "База данных (*.json)")[0]
        if fname:
            with open(fname, 'r', encoding='utf-8') as file:
                schema = json.load(file)
            self.tabWidget.clear()
            for q in schema:
                wid = self.addQuestion()
                wid.setValues(q)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    test = SchemaConstructor()
    test.show()
    sys.exit(app.exec_())
