from selenium import webdriver
import time
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import urllib.parse as urlparse

from PyQt5.QtCore import QThread, QObject, QAbstractTableModel, Qt
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox, QWidget
from PyQt5.uic import loadUi

import sys
import csv


def get_place_data(driver, city, address):  
    def is_bad_data(data):
        # дефолтный ответ - центр Киева. Исключаем это
        lon, lan = coord.split(',')
        lon, lan = float(lon), float(lan)
        return 30 < lon < 31 and 50 < lan < 51
    url = 'https://yandex.ua/maps'
    if address == '':
        return None
    find_text = city + ' ' + address
    driver.get(url)
    text_input_element = driver.find_element_by_class_name('suggest').find_element_by_tag_name('input') 
    text_input_element.send_keys(find_text)
    button_element = driver.find_element_by_css_selector("button[type='submit']")
    button_element.click()
    parsed = urlparse.urlparse(driver.current_url)
    coord = urlparse.parse_qs(parsed.query)['ll'][0]
    counter = 0
    while is_bad_data(coord):
        time.sleep(1)
        parsed = urlparse.urlparse(driver.current_url)
        coord = urlparse.parse_qs(parsed.query)['ll'][0]
        counter += 1
        if counter == 5:
            driver.save_screenshot('adress_parser_fail.png')
            break
    if is_bad_data(coord):
        return None
    else:
        lon, lan = coord.split(',')
        lon, lan = float(lon), float(lan)
        time.sleep(1)
        try:
            place_address = driver.find_element_by_css_selector('.business-card-view__address > span[itemprop="address"]').text
        except NoSuchElementException:
            place_address = None
        try:
            place_type = driver.find_element_by_css_selector('.business-card-title-view__category').text      
        except NoSuchElementException:
            place_type = None      
        try:
            place_name = driver.find_element_by_css_selector('h1.card-title-view__title').text
        except NoSuchElementException:
            place_name = None
        return {
        'longitude': lon, 
        'latitude': lan,
        'place_name': place_name,
        'place_address': place_address,
        'place_type': place_type
        }


class ParsingWorker(QObject):
    def __init__(self, parent, input_data):
        '''
        input data - список кортежей формата [('Название места', номер строки в TableModel),]
        '''
        super().__init__()
        self.input_data = input_data
        self.parent = parent
        try:
            self.driver = webdriver.Chrome('data\\chromedriver.exe')
        except Exception as e:
            QMessageBox.critical(self.parent, 'Ошибка веб-драйвера', str(e))
            self.driver = None

    def work(self):
        if self.driver:
            for item in self.input_data:
                city = self.parent.prefixLineEdit.text()
                address = item[0]            
                try:
                    data = get_place_data(self.driver, city, address)
                except Exception as e:
                    QMessageBox.critical(self.parent, 'Ошибка поиска', str(e))
                    self.quit()
                self.parent.model.addPlaceData(item[1], data)
            self.driver.quit()


class PlaceModel(QAbstractTableModel):
    def __init__(self, places=None):
        super(PlaceModel, self).__init__()
        self.items = None
        self.header_labels = None

    def data(self, index, role):
        if role == Qt.DisplayRole or role == Qt.EditRole:
            text = self.items[index.row()][index.column()]
            return text
        if role == Qt.BackgroundRole:
            if index.column()>=len(self.items[0])-5:
                return QBrush(QColor(255,255,0))

    def update(self, data):
        self.items = [i+[None]*5 for i in data]
        self.header_labels = [None]*len(data) + ['PlaceName', 'PlaceType', 'PlaceAddress', 'Longitude', 'Langitude']
        self.layoutChanged.emit()

    def addPlaceData(self, row, data):
        if data:
            self.items[row][-5] = data['place_name']
            self.items[row][-4] = data['place_type']
            self.items[row][-3] = data['place_address']
            self.items[row][-2] = data['longitude']
            self.items[row][-1] = data['latitude']
            self.layoutChanged.emit()

    def rowCount(self, index):
        if self.items:
            return len(self.items)
        else:
            return -1

    def columnCount(self, index):
        if self.items:
            return len(self.items[0])
        else:
            return -1

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal and self.header_labels:
            return self.header_labels[section]

    def setData (self, index, value, role):
        if role == Qt.EditRole and value:
            self.items[index.row()][index.column()] = value
            return True
        else:
            return False

    def flags(self, index):
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable


class AddressParserWidget(QWidget):    
    def __init__(self, parent=None):
        super().__init__()
        loadUi('data\\AddressParserWidget.ui', self)

        self.model = PlaceModel()
        self.tableView.setModel(self.model)
        self.driver = None

        self.signalsInit()
        self.show()

    def signalsInit(self):
        self.importCSVButton.clicked.connect(self.importCSV)
        self.exportCSVButton.clicked.connect(self.exportCSV)
        self.runButton.clicked.connect(self.runParsing)
        self.stopButton.clicked.connect(self.stopButtonActions)

    def stopButtonActions(self):
        self.thread.terminate()
        self.stopButton.setEnabled(False)
        self.runButton.setEnabled(True)

    def importCSV(self):
        fname = QFileDialog.getOpenFileName(
            self, 'Открыть таблицу', '.', "(*.csv)")[0]
        if fname:
            encoding = self.encodingBox.currentText()
            try:
                with open(fname, encoding=encoding) as f:
                    csv_file = csv.reader(f, delimiter=';')
                    data = []
                    for line in csv_file:
                        data.append(line)
                self.model.update(data)
            except UnicodeDecodeError:
                QMessageBox.warning(self, 'Ошибка чтения', 'Попробуйте другую кодировку', QMessageBox.Ok)

    def exportCSV(self):
        fname = QFileDialog.getSaveFileName(
            self, 'Сохранить таблицу', '.', "(*.csv)")[0]
        if fname:
            data = [self.model.header_labels] + self.model.items
            with open(fname, 'w', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerows(data)

    def runParsing(self):
        selectedIndexes = self.tableView.selectedIndexes()
        if not selectedIndexes:
            QMessageBox.warning(self, 'Ошибка', 'Выберите ячейки с названиями мест, которые необходимо найти', QMessageBox.Ok)
            return False
        input_data = [(self.model.data(i, Qt.DisplayRole), i.row()) for i in selectedIndexes]
        self.stopButton.setEnabled(True)
        self.runButton.setEnabled(False)
        self.thread = QThread()
        self.worker = ParsingWorker(self, input_data)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.work)
        self.thread.start()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    apw = AddressParserWidget()
    sys.exit(app.exec_())
