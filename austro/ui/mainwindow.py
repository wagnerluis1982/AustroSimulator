import os

from PySide.QtGui import *
from PySide.QtCore import Qt, QSize
from PySide.QtDeclarative import QDeclarativeView
from PySide.QtUiTools import QUiLoader

from austro.simulator.cpu import CPU
from austro.ui.codeeditor import CodeEditor
from austro.ui.models import MemoryModel


def _resource(*rsc):
    directory = os.path.dirname(__file__).decode("utf8")
    return os.path.join(directory, *rsc)


class MainWindow(object):
    def __init__(self):
        loader = QUiLoader()
        loader.registerCustomWidget(CodeEditor)
        self.gui = loader.load(_resource('mainwindow.ui'))
        gui = self.gui

        # Assembly editor get focus on start
        self.asmEdit = gui.findChild(CodeEditor, "asmEdit")
        self.asmEdit.setFocus()

        # Set QML file
        cpuDiagram = gui.findChild(QDeclarativeView, "cpuDiagram")
        cpuDiagram.setSource(_resource('qml', 'computer.qml'))

        #
        # In the following, define size factor for each splitted region.
        #
        mainsplitter = gui.findChild(QSplitter, "mainsplitter")
        mainsplitter.setStretchFactor(0, 3)
        mainsplitter.setStretchFactor(1, 8)
        mainsplitter.setStretchFactor(2, 3)

        leftsplitter = gui.findChild(QSplitter, "leftsplitter")
        leftsplitter.setStretchFactor(0, 2)
        leftsplitter.setStretchFactor(1, 1)
        leftsplitter.setStretchFactor(2, 1)

        middlesplitter = gui.findChild(QSplitter, "middlesplitter")
        middlesplitter.setStretchFactor(0, 2)
        middlesplitter.setStretchFactor(1, 1)

        # Models
        self.memoryModel = MemoryModel(CPU.ADDRESS_SPACE)
        memoryModel = self.memoryModel

        # Get trees
        self.tblMemory = gui.findChild(QTableView, "tblMemory")
        tblMemory = self.tblMemory
        tblMemory.setModel(memoryModel)
        tblMemory.resizeColumnToContents(0)

    def show(self):
        self.gui.show()
