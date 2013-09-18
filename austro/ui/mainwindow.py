import os

from PySide.QtGui import *
from PySide.QtCore import Qt, QSize
from PySide.QtDeclarative import QDeclarativeView
from PySide.QtUiTools import QUiLoader

from austro.asm import assembler
from austro.simulator.cpu import CPU
from austro.ui.codeeditor import CodeEditor, AssemblyHighlighter
from austro.ui.models import DataModel, MemoryModel


def _resource(*rsc):
    directory = os.path.dirname(__file__).decode("utf8")
    return os.path.join(directory, *rsc)


class MainWindow(object):
    def __init__(self):
        self.cpu = CPU()
        cpu = self.cpu

        loader = QUiLoader()
        loader.registerCustomWidget(CodeEditor)
        self.gui = loader.load(_resource('mainwindow.ui'))
        gui = self.gui

        # Assembly editor get focus on start
        self.asmEdit = gui.findChild(CodeEditor, "asmEdit")
        self.asmEdit.setFocus()
        AssemblyHighlighter(self.asmEdit.document())

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
        self.memoryModel = MemoryModel(cpu.memory)
        memoryModel = self.memoryModel

        # Get trees
        self.tblMemory = gui.findChild(QTableView, "tblMemory")
        tblMemory = self.tblMemory
        tblMemory.setModel(memoryModel)
        tblMemory.resizeColumnToContents(0)

        #
        ## Actions
        #
        self.actionLoad = gui.findChild(QAction, "actionLoad")
        self.actionLoad.triggered.connect(self.loadAssembly)

        self.actionRun = gui.findChild(QAction, "actionRun")

        self.actionStep = gui.findChild(QAction, "actionStep")

        self.actionStop = gui.findChild(QAction, "actionStop")
        self.actionStop.triggered.connect(self.stopAction)

    def loadAssembly(self):
        editor = self.asmEdit
        assembly = editor.toPlainText()
        asmd = assembler.assemble(assembly)

        self.cpu.reset()
        self.cpu.set_memory_block(asmd['words'])
        self.memoryModel.refresh()

        self.actionLoad.setEnabled(False)
        self.actionRun.setEnabled(True)
        self.actionStep.setEnabled(True)
        self.actionStop.setEnabled(True)

    def stopAction(self):
        self.actionLoad.setEnabled(True)
        self.actionRun.setEnabled(False)
        self.actionStep.setEnabled(False)
        self.actionStop.setEnabled(False)

    def show(self):
        self.gui.show()
