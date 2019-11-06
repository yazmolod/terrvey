import sys
import os
import traceback

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi

import re
import json
from data_base import DBController
from csv_parser import CSVParser
from recognizer import ImageRecognizer
from schema_constructor import SchemaConstructor


class QuestionWidget(QWidget):

    def __init__(self, json_dict):
        super().__init__()
        # сокращение слишком длинного текста, в символах
        self.label_max_size = 60
        self.question_type = json_dict['type']
        self.loadUi(json_dict)
        self.setObjectName(json_dict['table_name'])
        widgets = self.findChildren(QWidget)
        self.answer_items = [i for i in widgets if 'dbSubject' in i.objectName()]


    def loadUi(self, json_dict):
        title = QLabel(json_dict['quest'])
        title.setWordWrap(True)
        grid = QGridLayout()
        grid.addWidget(title, 0, 0, 1,0)

        # служит для группировки кнопок по exclusive
        self.button_groups = []

        #текст
        if json_dict['type'] == 'text' or json_dict['type'] == 'mtext':
            label = QLabel('Ответ:')
            te = QTextEdit()
            te.setObjectName ('dbSubject')
            te.db_value = ''
            grid.addWidget(label, 1, 0)
            grid.addWidget(te, 1, 1, 3, 1)

        # матричный выбор
        elif json_dict['type'] == 'matrix' or json_dict['type'] == 'mmatrix':
            options_count = len(json_dict['answer_options'])
            for i in range(options_count):
                label_top = QLabel(json_dict['answer_options'][i])
                label_top.setMaximumWidth(50)
                grid.addWidget(label_top, 0, i+1)
            for i in range(len(json_dict['answers'])):
                label_side = QLabel(json_dict['answers'][i])
                grid.addWidget(label_side, i+2, 0)
                self.button_groups.append(QButtonGroup(self))
                for j in range(options_count):
                    if json_dict['type'] == 'mmatrix':
                        btn = QCheckBox()
                    else:
                        btn = QRadioButton()
                        self.button_groups[i].addButton(btn)
                    btn.setObjectName ('dbSubject')
                    btn.db_value = json_dict['answers'][i]
                    btn.column_index = j
                    btn.row_index = i                    
                    grid.addWidget(btn, i+2, j+1)      
        
        # опциональный выбор          
        else:
            for i in range(len(json_dict['answers'])):
                if json_dict['type'] in ('mopt', 'mopt+'):
                    btn = QCheckBox()
                else:
                    btn = QRadioButton()
                btn.setObjectName ('dbSubject')
                btn.row_index = i
                btn.db_value = json_dict['answers'][i]
                btn.setText(str(i+1))
                lbl = QLabel(json_dict['answers'][i])
                lbl.setWordWrap(True)
                grid.addWidget(lbl, i+1, 0)
                grid.addWidget(btn, i+1, 1)
                # горячая клавиша
                answer_number = i+1
                if answer_number < 10:
                    shortcut = QShortcut(str(answer_number), self)
                elif 10 <= answer_number < 20:
                    shortcut = QShortcut('Ctrl+' + str(answer_number % 10), self)
                elif 20 <= answer_number < 30:
                    shortcut = QShortcut('Alt+' + str(answer_number % 20), self)
                else:
                    shortcut = QShortcut('Ctrl+Alt' + str(answer_number % 30), self)
                shortcut.activated.connect(btn.nextCheckState)
        
        # ДРУГОЕ
            if json_dict['type'] in ('opt+', 'mopt+'):
                label = QLabel('Другое')
                # if json_dict['type'] in ('mopt', 'mopt+'):
                #     btn = QCheckBox()
                # else:
                #     btn = QRadioButton()
                # btn.setObjectName ('AnotherFlag')
                le = QLineEdit()
                le.setObjectName ('dbSubject')
                le.db_value = ''
                grid.addWidget(label, i+2, 0)
                # grid.addWidget(btn, i+2, 1)
                grid.addWidget(le, i+2, 1)
        self.setLayout(grid)


    def get_values(self):
        if self.question_type in ('matrix', 'mmatrix'):
            # Тут нужно что-то починить
            values = [[] for i in range(self.parent().parent().parent().PROJECT['MATRIX_WIDTH'][self.objectName()])]
        else:
            values = []
        for i in self.answer_items:
            if (type(i) == QRadioButton or type(i) == QCheckBox) and (self.question_type=='opt' or self.question_type=='mopt'):
                if i.isChecked():
                	values.append(i.db_value)
            elif (type(i) == QRadioButton or type(i) == QCheckBox) and (self.question_type=='opt+' or self.question_type=='mopt+'):
                if i.isChecked():
                    values.append((i.db_value, 0))
            elif type(i) == QRadioButton or type(i) == QCheckBox and self.question_type in ('matrix', 'mmatrix'):
                if i.isChecked():
                    values[i.column_index].append(i.db_value)
            elif type(i) == QLineEdit and self.question_type in ('opt+', 'mopt+'):
                text = i.text()
                if text:
                    values.append((text, 1))
            elif type(i) == QTextEdit and self.question_type in ('text', 'mtext'):
                values.append(i.toPlainText())
        return values


    def set_values(self, values):
        for ivalue in range(len(values)):
            if self.question_type == 'opt' or self.question_type == 'mopt':
                for i in self.answer_items:
                    if i.db_value == values[ivalue]:
                        i.setChecked(True)
                        break

            elif self.question_type == 'opt+' or self.question_type == 'mopt+':
                if values[ivalue][1] == 0:
                    for i in self.answer_items:
                        if i.db_value == values[ivalue][0]:
                            i.setChecked(True)
                            break
                else:
                    for i in self.answer_items:
                        if type(i) == QLineEdit:
                            i.setText(values[ivalue][0])
                            break

            elif self.question_type == 'matrix' or self.question_type == 'mmatrix':
                column_index = ivalue
                for j in values[ivalue]:
                    for i in self.answer_items:
                        if i.db_value == j and i.column_index == column_index:
                            i.setChecked(True)
            elif self.question_type == 'text' or self.question_type == 'mtext':
                self.answer_items[0].setPlainText(values[ivalue])

    def reset(self):
        for i in self.button_groups:
            i.setExclusive(False)
        for i in self.answer_items:
            if type(i) == QRadioButton:
                i.setAutoExclusive(False)
                i.setChecked(0)
                i.setAutoExclusive(True)
            elif type(i) == QCheckBox:
                i.setChecked(0)
            elif type(i) == QComboBox:
                i.setCurrentIndex(-1)
            elif type(i) == QLineEdit:
                i.setText("")
            elif type(i) == QTextEdit or type(i) == QPlainTextEdit:
                i.setPlainText("")
        for i in self.button_groups:
            i.setExclusive(True)


class ImageRecognizerSetup(QDialog):

    def __init__(self, parent=None, ir_settings=None):
        super(ImageRecognizerSetup, self).__init__(parent)
        loadUi('ui\\ImageRecognizerSetup.ui', self)     
        self.showMaximized()   
        self.init_data_structure()
        self.init_question_info()
        self.init_signals()
        # Здесь хранятся кортежи формата (QPointF, QGraphicsRectItem)
        self.mark_collection = [] 
        # настройка экрана рисования  
        self.graphicsScene = QGraphicsScene(self)
        self.graphicsView.setScene(self.graphicsScene)
        self.graphicsView.mousePressEvent = self.mousePressEvent  
        # первоначальные данные    
        self.rect_size = self.rectSizeSlider.minimum()        
        self.resp_regexp = self.regexpRespText.text()
        self.side_regexp = self.regexpSideText.text()
        if ir_settings:
            self.ir_settings = ir_settings
        else:
            self.ir_settings = {}
        self.update_settings_view()
        self.draw_mode = False
        # контур для марок
        self.pen = QPen()
        self.pen.setWidth(2)
        self.pen.setColor(QColor(255,0,0))
        # показ
        self.exec_()

    def init_signals(self):
        self.filePathButton.clicked.connect(self.selectFile)
        self.filePathText.textChanged.connect(self.load_image)
        self.rectSizeSlider.valueChanged.connect(lambda x: self.set_rect_size(x))        
        self.deleteLastRectButton.clicked.connect(self.delete_last_rect)
        self.deleteAllRectButton.clicked.connect(self.delete_all_rect)
        self.deleteAllRectButton.clicked.connect(self.delete_all_rect)
        self.regexpRespText.textChanged.connect(self.set_resp_regexp)
        self.regexpSideText.textChanged.connect(self.set_side_regexp)
        self.filePathText.textChanged.connect(self.path_changed)
        self.saveSettingsButton.clicked.connect(self.save_settings)
        self.loadSettingsButton.clicked.connect(self.load_settigns)

    def save_settings(self):
        path = QFileDialog.getSaveFileName(
        self, 'Сохранить настройки для считывания', '.', "Файл (*.json)")[0]
        if path:
            with open(path, 'w') as f:
                json.dump(self.ir_settings, f)

    def load_settigns(self):
        path = QFileDialog.getOpenFileName(
        self, 'Открыть настройки для считывания', '.', "Файл (*.json)")[0]
        if path:
            with open(path) as f:
                self.ir_settings = json.load(f)
                self.update_settings_view()


    def path_changed(self, t):
        self.set_resp_regexp(t)
        self.set_side_regexp(t)

    def set_resp_regexp(self, t):
        regexp = self.regexpRespText.text()
        path = self.filePathText.text().split('/')[-1]
        if path:
            try:
                re_result = re.findall(regexp, path)
            except:
                self.regexpRespResultText.clear()
            else:
                if len(re_result) == 1:
                    self.regexpRespResultText.setText(re_result[0])
                else:
                    self.regexpRespResultText.clear()

    def set_side_regexp(self, t):
        regexp = self.regexpSideText.text()
        path = self.filePathText.text().split('/')[-1]
        if path:
            try:
                re_result = re.findall(regexp, path)
            except:
                self.regexpSideResultText.clear()
            else:
                if len(re_result) == 1:
                    self.regexpSideResultText.setText(re_result[0])
                else:
                    self.regexpSideResultText.clear()

    def set_rect_size(self, x):
        self.rect_size = x

    def delete_last_rect(self):
        if self.mark_collection:
            mark = self.mark_collection.pop()
            self.graphicsScene.removeItem(mark[1])

    def delete_all_rect(self):
        for i in range(len(self.mark_collection)):
            mark = self.mark_collection.pop()
            self.graphicsScene.removeItem(mark[1])

    def marking_process(self, state):
        self.draw_mode = state
        if state:
            self.delete_all_rect()
        else:
            result = {}
            result['regions'] = [mark[1].rect().toRect().getCoords() for mark in self.mark_collection]
            result['side'] = self.regexpSideResultText.text()
            table_name = self.sender().table_name
            column_name = self.sender().column_name
            if column_name:
                self.ir_settings[table_name+'>'+column_name] = result
            else:
                self.ir_settings[table_name] = result
            self.update_settings_view()

    def update_settings_view(self):
        self.textEdit.setText(str(self.ir_settings))  

    def init_question_info(self):
        for q in self.data_structure:
            wid = QWidget()
            layout =  QVBoxLayout(wid)
            lbl1 = QLabel(q[1])
            lbl1.setWordWrap(True)
            lbl_msg = 'Строк: {}'.format(q[2])
            if q[3] > 1:
                lbl_msg += ', Столбцов (в случае матрицы): {}\nВНИМАНИЕ: ВЫДЕЛЯТЬ В ПОРЯДКЕ ВСЕ СТРОКИ - ПЕРЕХОД К СЛЕДУЮЩЕМУ СТОЛБЦУ'.format(q[3])
            lbl2 = QLabel(lbl_msg)
            lbl2.setWordWrap(True)
            btn = QPushButton('Поставить отметки по вопросу')
            btn.table_name = q[0]
            btn.column_name = q[4]
            btn.toggled.connect(self.marking_process)
            btn.setCheckable(True)
            layout.addWidget(lbl1)
            layout.addWidget(lbl2)
            layout.addWidget(btn)
            self.tabWidget.addTab(wid, q[0])

    def init_data_structure(self):
        self.data_structure = []
        for item in self.parent().PROJECT['STRUCTURE']:
            if 'text' not in item['type']:
                name = item['table_name']
                question = item['quest']
                rows = len(item['answers'])
                cols = len(item.get('answer_options', [1]))
                col_name = item.get('table_column', None)
                self.data_structure.append((name, question, rows, cols, col_name))

    def selectFile(self):
        self.filePathText.setText(QFileDialog.getOpenFileName(self, 'Шаблон изображения', '.', "Изображение (*.jpg)")[0])

    def load_image(self, text):
        pixmap = QPixmap(text)
        pixmap_item = QGraphicsPixmapItem(pixmap)
        self.graphicsScene.addItem(pixmap_item)

    def mousePressEvent(self, e):
        if self.draw_mode:
            point = self.graphicsView.mapToScene(e.pos())
            rect = self.graphicsScene.addRect(point.x()-self.rect_size/2, point.y()-self.rect_size/2, 
                                            self.rect_size, self.rect_size, self.pen)
            self.mark_collection.append((point, rect))


class ImportCSVDialog(QDialog):

    def __init__(self, parent=None):
        super(ImportCSVDialog, self).__init__(parent)
        loadUi('ui\\ImportCSVDialog.ui', self)
        self.filePathButton.clicked.connect(self.selectFile)
        self.startButton.clicked.connect(self.process)
        # проверка значений
        validator = QIntValidator()
        validator.setBottom(1)
        self.startRespondentText.setValidator(validator)
        self.startRowText.setValidator(validator)
        self.stopRowText.setValidator(validator)
        self.exec_()

    def process(self):
        path, options = self.getOptions()
        parser = CSVParser(path, self.parent().PROJECT['STRUCTURE'])
        self.progressBar.setMaximum(parser.csv_row_count-options['have_header'])
        counter = 0
        for row in parser.parse_all(**options):
            if counter % 100 == 0:
                self.parent().DB.set_values(row, commit=True)
            else:
                self.parent().DB.set_values(row, commit=False)
            counter += 1
            self.progressBar.setValue(counter)
        self.parent().DB.hard_commit()
        self.accept()

    def selectFile(self):
        self.filePathText.setText(QFileDialog.getOpenFileName(self, 'Открыть результаты онлайн-опроса', '.', "Текстовый документ (*.csv)")[0])

    def getOptions(self):
        path = self.filePathText.text()
        result = {}
        result['start_respondentid'] = int(self.startRespondentText.text())
        result['start_row'] = int(self.startRowText.text())
        if len(self.stopRowText.text())>0:
            result['stop_row'] = int(self.stopRowText.text())
        result['have_header'] = self.haveHeaderBox.isChecked()
        return path, result


class MainApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initStartDialog()

    def __getattr__(self, attr):
        print (attr, ' does not exist!')
        return None

    def initStartDialog(self):
        startDialog = QDialog(self)
        loadUi('ui\\StartDialog.ui', startDialog)
        resolution = QDesktopWidget().screenGeometry()
        startDialog.move((resolution.width() / 2) - (startDialog.frameSize().width() / 2),
                         (resolution.height() / 2) - (startDialog.frameSize().height() / 2))
        open_btn = startDialog.buttonBox.button(QDialogButtonBox.Open)
        save_btn = startDialog.buttonBox.button(QDialogButtonBox.Save)
        open_btn.clicked.connect(self.openProjectDialog)
        save_btn.clicked.connect(self.newProjectDialog)
        ret = startDialog.exec_()
        if ret == QDialog.Accepted:
            loadUi('ui\\MainWorkflow.ui', self)
            self.initUI()
        else:
            sys.exit()

    def initUI(self):
        self.show()
        # Задаем такой размер, чтобы автоматически получить самую компактную конфигурацию
        self.resize(1,1)
        self.setWindowTitle('Terrvey v0.1 - '+self.DB.path)
        self.setWindowIcon(QIcon('media/icon.png'))

        # Статус бар
        self.status = self.statusBar()
        self.status.showMessage('Ready')

        # Палитры для индетификации наличия анкеты в базе
        self.palette_good = QPalette()
        self.palette_bad = QPalette()
        self.palette_good.setColor(QPalette.Text, QColor(0, 90, 0))
        self.palette_good.setColor(QPalette.Highlight, QColor(0, 90, 0))        
        self.palette_bad.setColor(QPalette.Text, QColor(255, 0, 0))
        self.palette_bad.setColor(QPalette.Highlight, QColor(255, 0, 0))

        # Добавляем в QStackedWidget все заготовки формата .ui
        self.question_widgets = []
        for i in self.PROJECT['STRUCTURE']:
            if 'Quest' in i['table_name']:
                wid = QuestionWidget(i)
                self.question_widgets.append(wid)
                self.Stack.addWidget(wid)

        # Показ и управление текущего респондента
        self.update_respondent_count()     

        # проверка значений для возраста
        validator = QIntValidator()
        validator.setRange(0,100)
        self.AgeBox.setValidator(validator)

        # Загрузка данных в комбобоксы
        self.DistrictBox.addItems(self.PROJECT['DEFAULT_VALUES']['Districts'])
        self.GenderBox.addItems(self.PROJECT['DEFAULT_VALUES']['Genders'])
        self.SourceBox.addItems(self.PROJECT['DEFAULT_VALUES']['Sources'])

        # Первоначальная загрузка данных из БД по текущему респонденту
        self.load_values()

        # Блок управления текущим вопросом
        self.questSpinBox.setMaximum(len(self.question_widgets))
        self.questSpinBox.valueChanged.connect(
            lambda x: self.Stack.setCurrentIndex(x - 1))
        self.NextButton.clicked.connect(self.on_next_clicked)
        self.BackButton.clicked.connect(self.on_back_clicked)
        self.SaveButton.clicked.connect(self.on_save_clicked)
        self.newFormButton.clicked.connect(self.on_newform_clicked)
        self.resetAllButton.clicked.connect(self.on_reset_all_clicked)
        self.resetCurrentButton.clicked.connect(self.on_reset_current_clicked)
        self.currentForm.valueChanged.connect(self.update_window)
        self.deleteCurrentButton.clicked.connect(self.delete_current)

        # Настройка сигналов для кнопок
        self.importCSVButton.clicked.connect(self.importCSV_clicked)
        self.IRSetupButton.clicked.connect(self.IRSetup_clicked)
        self.IRProcess.clicked.connect(self.IRProcess_clicked)

        #горячие клавиши
        next_form_shortcut = QShortcut(QKeySequence(Qt.Key_Up), self)
        next_form_shortcut.activated.connect(self.currentForm.stepUp)
        previous_form_shortcut = QShortcut(QKeySequence(Qt.Key_Down), self)
        previous_form_shortcut.activated.connect(self.currentForm.stepDown)

    def IRProcess_clicked(self):
        path = QFileDialog.getOpenFileName(self, 'Изображение', '.', "(*.jpg)")[0]
        if path:
            self.process_image(path)

    def IRSetup_clicked(self):
        dialog = ImageRecognizerSetup(self, self.ir_settings)
        if dialog:
            self.ir_settings = dialog.ir_settings
            self.ir_settings_additional = {
                                'Respondent_re': dialog.resp_regexp,
                                'Side_re': dialog.side_regexp,
                                }
        else:
            pass

    def importCSV_clicked(self):
        dialog = ImportCSVDialog(self)
        if dialog:
            QMessageBox.information(self, "Импорт CSV", "Импорт завершен")
        else:
            QMessageBox.information(self, "Импорт CSV", "Импорт отменен")
        self.update_window()

    def process_image(self, path):
        # Считывает данные с изображения по заранее заготовленному
        # конфигу, хранящемся в self.ir_settings
        raw_values = {}
        if self.ir_settings:
            side = re.findall(self.ir_settings_additional['Side_re'], path.split('/')[-1])[0]
            resp_id = re.findall(self.ir_settings_additional['Respondent_re'], path.split('/')[-1])[0]
            resp_id = int(resp_id)
            raw_values['Respondents>RespondentId'] = resp_id            
            for table_name, settings in self.ir_settings.items():
                if settings['side'] == side:
                    recognizer = ImageRecognizer(src_path=path, example_path="2rd stage\example_image\B.jpg", regions=settings['regions'])
                    raw_values[table_name] = recognizer.get_values()
            print (raw_values)
            self.process_recognized_values(raw_values)
        else:
            QMessageBox.warning(self, "Ошибка", "Не задан файл-конфиг для распознания", QMessageBox.Ok)

    def process_recognized_values(self, raw_values):
        result_values = {}
        for key in raw_values:
            value = raw_values[key]
            if '>' in key:
                table_name, table_column = key.split('>')
                if result_values.get(table_name, None) == None:
                    result_values[table_name] = {}
            else:
                table_name, table_column = key, None
            for j in self.PROJECT['STRUCTURE']:
                # развитие инфы на стандартную схему
                if j['table_name'] == table_name and j.get('table_column', None) == table_column:
                    answers = j['answers']
                    table_type = j['type']
                    # обычный выбор
                    if table_type in ('opt', 'mopt'):
                        v = [answers[i] for i in range(len(value)) if value[i]]
                    # с другое
                    elif table_type in ('opt+', 'mopt+'):
                        v = [(answers[i], 0) for i in range(len(value)) if value[i]]
                    # матрицы ТРЕБУЕТ РЕАЛИЗАЦИИ
                    elif table_type in ('matrix', 'mmatrix'):
                        pass
                # проверка вложенной инфы типа Respondents
            if table_column:
                result_values[table_name][table_column] = v
            else:
                result_values[table_name] = v
        print (result_values)
        #self.load_values(result_values, False)

    def delete_current(self):
        resp_id = self.currentForm.value()
        if resp_id in self.DB.get_all_resp_id():
            reply = QMessageBox.question(self, 'Предупреждение', 
                     'Удаление данного респондента будет безвозвратным. Вы уверены?', QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.DB.delete_resp(resp_id)
                QMessageBox.information(self, "", "Респондет №%d удален из базы" % resp_id)
        else:
            QMessageBox.information(self, "", "Респондет №%d отсутствует в базе" % resp_id)
        self.update_window()

    def update_respondent_count(self):
        last_resp_id = self.DB.get_last_resp_id()
        if last_resp_id:
            self.countForm.setText('/' + str(last_resp_id))
            self.currentForm.setMaximum(last_resp_id)
        else:
            self.countForm.setText('/1')
            self.currentForm.setMaximum(1)

    def update_window(self):
        self.questSpinBox.setValue(1)
        self.update_respondent_count()
        self.load_values()
        if self.currentForm.value() in self.DB.get_all_resp_id():
            self.currentForm.setPalette(self.palette_good)
        else:
            self.currentForm.setPalette(self.palette_bad)

    def load_values(self, direct_values=None, reset=True):
        '''Загружает данные из БД в виджеты по данному респонденту'''
        current_resp = self.currentForm.value()
        if reset:
            self.reset_all()
        if current_resp in self.DB.get_all_resp_id() and not direct_values:            
            values = self.DB.get_values(current_resp)
        elif direct_values:
            values = direct_values
        else:
            values = {}
        source = values.get('Respondents', {}).get('Source', None)
        age = values.get('Respondents', {}).get('Age', None)
        address = values.get('Respondents', {}).get('Address', None)
        district = values.get('Respondents', {}).get('District', None)
        gender = values.get('Respondents', {}).get('Gender', None)
        if source:
            self.SourceBox.setCurrentIndex(self.SourceBox.findText(source))
        if district:
            self.DistrictBox.setCurrentIndex(self.DistrictBox.findText(district))            
        if gender:
            self.GenderBox.setCurrentIndex(self.GenderBox.findText(gender))
        if age:
            self.AgeBox.setText(str(age))
        if address:
            self.AddressBox.setText(address)
        for wid in self.question_widgets:
            wid.set_values(values.get(wid.objectName(), []))
        self.status.showMessage('Form #%d is loaded' % (current_resp))

    def save_values(self):
        '''Сохраняет данные по данному респонденту в БД'''
        values = {i.objectName(): i.get_values()
                       for i in self.question_widgets}
        values['Respondents'] = {}
        values['Respondents']['Source'] = self.SourceBox.currentText()
        values['Respondents']['District'] = self.DistrictBox.currentText()
        values['Respondents']['RespondentId'] = self.currentForm.value()
        values['Respondents']['Gender'] = self.GenderBox.currentText()
        values['Respondents']['Address'] = self.AddressBox.text()
        if self.AgeBox.text():
            values['Respondents']['Age'] = int(self.AgeBox.text())
        try:
            self.DB.set_values(values)
            self.update_window()
        except:
            msg = QMessageBox.warning(self, "Ошибка доступа к базе данных",
                                        "База данных в данный момент занята, попробуйте позже", QMessageBox.Ok)

    def reset_current(self):
        self.Stack.currentWidget().reset()

    def reset_all(self):
        self.GenderBox.setCurrentIndex(0)
        self.DistrictBox.setCurrentIndex(0)
        self.AddressBox.setText('')
        self.AgeBox.setText('')
        for wid in self.question_widgets:
            wid.reset()

    def on_reset_all_clicked(self):
        self.reset_all()

    def on_reset_current_clicked(self):
        self.reset_current()

    def on_save_clicked(self):
        self.save_values()
        current_resp = self.currentForm.value()
        self.status.showMessage('Updated form: #' + str(current_resp))

    def dragEnterEvent(self, e):
        e.accept()

    def dropEvent(self, e):
        # обработка по типу файлов не реализована!
        if True:
            for url in e.mimeData().urls():
                self.process_image(url.toLocalFile())

    def on_newform_clicked(self):
        old_count = self.currentForm.value()
        try:
            # Случай, когда нет даже первой анкеты и метод выбрасывает None
            new_count = self.DB.get_last_resp_id() + 1
        except TypeError:
            buttonReply = QMessageBox.warning(self, "Не могу создать новую анкету",
                                              "Первая анкета пустая. Сначала заполните ее!", QMessageBox.Ok)
        else:
            if old_count == new_count:
                # Случай, если в программе висит крайняя анкета, которая еще не занесена в базу
                buttonReply = QMessageBox.warning(self, "Не могу создать новую анкету",
                                                  "Крайняя анкета не сохранена или пустая. Разберитесь с ней!", QMessageBox.Ok)
            else:
                self.DB.add_empty_resp()
                self.currentForm.setValue(new_count)
                self.questSpinBox.setValue(1)
                self.status.showMessage('Added new form: #%d' % (new_count))
        self.update_window()

    def on_next_clicked(self):
        self.Stack.setCurrentIndex(self.Stack.currentIndex() + 1)
        self.questSpinBox.setValue(self.questSpinBox.value() + 1)

    def on_back_clicked(self):
        self.Stack.setCurrentIndex(self.Stack.currentIndex() - 1)
        self.questSpinBox.setValue(self.questSpinBox.value() - 1)

    def openProjectDialog(self):
        fname = QFileDialog.getOpenFileName(
            self, 'Открыть проект опроса', '.', "Проект Terrvey (*.trv)")[0]
        if fname:
            with open(fname, 'r', encoding='utf-8') as file:
                self.PROJECT = json.load(file)
                self.PROJECT['PROJECT_PATH'] = fname
                self.PROJECT['DATABASE_PATH'] = fname.replace('.trv', '__DB.sqlite')
                self.DB = DBController(self.PROJECT)
        else:
            sys.exit()

    def newProjectDialog(self):
        schema = SchemaConstructor()
        schema.exec_()
        if schema:
            project_path = schema.project_path
            with open(project_path, 'r', encoding='utf-8') as file:
                self.PROJECT = json.load(file)
                self.PROJECT['PROJECT_PATH'] = project_path
                self.PROJECT['DATABASE_PATH'] = project_path.replace('.trv', '__DB.sqlite')
                self.DB = DBController(self.PROJECT)
        else:
            sys.exit()


if __name__ == '__main__':
#    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    app = QApplication(sys.argv)
    splash_pix = QPixmap('media/splash.jpg')
    splash = QSplashScreen(splash_pix)
    splash.show()
    app.processEvents()
    w = MainApp()
    splash.finish(w)
    sys.exit(app.exec_())
    w.DB.close()
