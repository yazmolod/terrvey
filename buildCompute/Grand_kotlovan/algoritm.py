import sys
from PyQt5 import QtCore, QtGui, QtWidgets

from PyQt5.uic import loadUi


class MyWin(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__()
        try:
            loadUi("./Grand_kotlovan/grandkotlovanUI.ui", self)
        except:
            loadUi("./grandkotlovanUI.ui", self)
        #self.statusbar.showMessage(
        #    '© Павел Маракаев, АО "Самаранефтехимпроект", 2020')

        # Вешаем на кнопку функцию Algoritm
        self.pushButton.clicked.connect(self.Algoritm)

    def Algoritm(self):
        # Извлекаем из поля Doublespinbox введенное цифровое значение ДЛИНЫ основания котлована
        length = self.doubleSpinBox_length.value()
        # Извлекаем из поля Doublespinbox введенное цифровое значение ШИРИНЫ основания котлована
        width = self.doubleSpinBox_width.value()
        # Извлекаем из поля Doublespinbox введенное цифровое значение ВЫСОТЫ котлована
        height = self.doubleSpinBox_height.value()

        # Расчет коэффициента крутизны откоса m в зависимости от типа грунта из выпад. списка (comboBox_ground_type) и высоты котлована (height)

        # для 1 - Насыпной неуплотненный
        m = None
        if self.comboBox_ground_type.currentText() == "Насыпной неуплотненный":
            if height <= 1.5:
                m = 0.67
            elif height <= 3:
                m = 1
            elif height <= 5:
                m = 1.25
        if self.comboBox_ground_type.currentText() == "Песчаный и гравийный":           # для 2 - Песчаный и гравийный
            if height <= 1.5:
                m = 0.5
            elif height <= 3:
                m = 1
            elif height <= 5:
                m = 1
        if self.comboBox_ground_type.currentText() == "Супесь":                          # для 3 - Супесь
            if height <= 1.5:
                m = 0.25
            elif height <= 3:
                m = 0.67
            elif height <= 5:
                m = 0.85
        if self.comboBox_ground_type.currentText() == "Суглинок":                        # для 4 - Суглинок
            if height <= 1.5:
                m = 0
            elif height <= 3:
                m = 0.5
            elif height <= 5:
                m = 0.75
        if self.comboBox_ground_type.currentText() == "Глина":                            # для 5 - Глина
            if height <= 1.5:
                m = 0
            elif height <= 3:
                m = 0.25
            elif height <= 5:
                m = 0.5
        if self.comboBox_ground_type.currentText() == "Лёссы и лёссовидные":             # для 6 - Лёссы и лёссовидные
            if height <= 1.5:
                m = 0
            elif height <= 3:
                m = 0.5
            elif height <= 5:
                m = 0.5
        # для 7 - Морёные песчаные и супесчаные
        if self.comboBox_ground_type.currentText() == "Морёные песчаные и супесчаные":
            if height <= 1.5:
                m = 0.25
            elif height <= 3:
                m = 0.57
            elif height <= 5:
                m = 0.75
        if self.comboBox_ground_type.currentText() == "Морёные суглинистые":             # для 8 - Морёные суглинистые
            if height <= 1.5:
                m = 0.2
            elif height <= 3:
                m = 0.5
            elif height <= 5:
                m = 0.65

        # Расчет длины верха котлована
        if m == None:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Значение вне диапазона")
            m = 0
            length_top = 0
            width_top = 0 
            V = 0
        else:
            length_top = (height * m) + length + (height * m)
            # Расчет ширины верха котлована
            width_top = (height * m) + width + (height * m)
            V = height / 6 * ((2 * width + width_top) * length + (2 *
                                                                  width_top + width) * length_top)  # Расчет объема котлована

        # Вывод коэффициента "m"
        self.doubleSpinBox_m.setValue(m)
        self.doubleSpinBox_length_top.setValue(
            length_top)         # Вывод длины верха котлована
        self.doubleSpinBox_width_top.setValue(
            width_top)           # Вывод ширины верха котлована
        # Вывод объема котлована
        self.doubleSpinBox_V.setValue(V)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    myapp = MyWin()
    myapp.show()
    sys.exit(app.exec_())
