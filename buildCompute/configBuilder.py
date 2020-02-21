from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi

class TreeItem(object):
	def __init__(self, parent, row):
		self._parent = parent
		self._row = row
		self._children = self._getChildren()

	def _getChildren(self):
		pass


class TreeModel(QAbstractItemModel):
	def __init__(self):
		super().__init__(self)


class ConfigConstructor(QDialog):
    def __init__(self, config):
        """Дмалог набора конфига"""
        super().__init__()        
        loadUi(r"./ui/configConstructor.ui", self)
        self.model = QStandardItemModel()
        self.treeView.setModel(self.model)

        self.buildTree(config)

    def buildTree(self, structure):    	
    	for work in structure:
    		workItem = QStandardItem(work.get("Name", ""))
    		for section in work.get("Sections", []):
    			sectionItem = QStandardItem(section.get("Name", ""))
    			for inp in section.get("Inputs", []):
    				inpItem = QStandardItem(inp.get("Name", ""))
    				sectionItem.appendRow(inpItem)
    			for out in section.get("Outputs", []):
    				outItem = QStandardItem(out.get("Name", ""))
    				sectionItem.appendRow(outItem)
    			workItem.appendRow(sectionItem)
    		self.model.appendRow(workItem)

