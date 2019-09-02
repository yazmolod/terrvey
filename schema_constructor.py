from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
import sys


class SchemaBrick(QWidget):
    def __init__(self):
        super().__init__()
        self.loadUI()

    def loadUI(self):
        self.questionTypes = [
        'Текст (строка)',
        'Текст (абзац)',
        'Один из списка',
        'Несколько из списка',
        'Матрица с одним выбором',
        'Матрица с несколькими выборомами'
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
        self.layout.addWidget(self.questionTypeComboBox, 0, 1)
        self.layout.addWidget(QLabel('Тип вопроса'), 0, 0)
        self.layout.addWidget(self.otherAnswerCheckBox, 1, 1)
        self.layout.addWidget(QLabel('Вариант "другое"'), 1, 0)
        self.layout.addWidget(self.questionTitleLineEdit, 2, 1)
        self.layout.addWidget(QLabel('Заголовок вопроса'), 2, 0)
        self.layout.addWidget(self.tableNameLineEdit, 3, 1)
        self.layout.addWidget(QLabel('Имя таблицы вопроса'), 3, 0)
        self.layout.addWidget(self.tableColumnLineEdit, 4, 1)
        self.layout.addWidget(QLabel('Имя столбца'), 4, 0)
        self.layout.addWidget(self.csvColumnSpinBox, 5, 1)
        self.layout.addWidget(QLabel('Столбец в CSV'), 5, 0)

        self.layout.addWidget(self.answersCountSpinBox, 0, 2)
        self.layout.addWidget(self.matrixColumnsCountSpinBox, 0, 3)
        self.setLayout(self.layout)


        self.answersCountSpinBox.setMinimum(0)
        self.matrixColumnsCountSpinBox.setMinimum(0)
        self.csvColumnSpinBox.setMinimum(1)
        self.questionTypeComboBox.addItems(self.questionTypes)
        self.questionTypeComboBox.setCurrentIndex(-1)

        self.questionTypeComboBox.currentIndexChanged.connect(self.typeChanged)
        self.answersCountSpinBox.valueChanged.connect(self.answersChanged)
        self.matrixColumnsCountSpinBox.valueChanged.connect(self.columnsChanged)

    def answersChanged(self, value):
        if value > len(self.answers):
            while len(self.answers) != value:
                le = QLineEdit()
                self.layout.addWidget(le, len(self.answers) + 1, 2)
                self.answers.append(le)
        else:
            while len(self.answers) != value:
                le = self.answers.pop()
                le.deleteLater()

    def columnsChanged(self, value):
        if value > len(self.columns):
            while len(self.columns) != value:
                le = QLineEdit()
                self.layout.addWidget(le, len(self.columns) + 1, 3)
                self.columns.append(le)
        else:
            while len(self.columns) != value:
                le = self.columns.pop()
                le.deleteLater()


    def typeChanged(self, index):
        self.answersCountSpinBox.setValue(0)
        self.matrixColumnsCountSpinBox.setValue(0)

        if index <= 1:
            self.answersCountSpinBox.setEnabled(False)
            self.matrixColumnsCountSpinBox.setEnabled(False)
        elif 1 < index < 4:
            self.answersCountSpinBox.setEnabled(True)
            self.matrixColumnsCountSpinBox.setEnabled(False)

        elif 4 <= index:
            self.answersCountSpinBox.setEnabled(True)
            self.matrixColumnsCountSpinBox.setEnabled(True)
        text = self.questionTypeComboBox.currentText()
        isOther = self.otherAnswerCheckBox.isChecked()


class SchemaConstructor(QWidget):
    def __init__(self):
        super().__init__()
        loadUi('ui\\SchemaConstructor.ui', self)
        self.initSignals()

    def initSignals(self):
        self.addButton.clicked.connect(self.addQuestion)
        self.removeButton.clicked.connect(self.removeQuestion)

    def addQuestion(self):
        wid = SchemaBrick()
        self.tabWidget.addTab(wid, '?')

    def removeQuestion(self):
        self.tabWidget.removeTab(self.tabWidget.currentIndex())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    test = SchemaConstructor()
    test.show()
    sys.exit(app.exec_())
