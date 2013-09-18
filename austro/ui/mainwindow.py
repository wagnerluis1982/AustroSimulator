import os

from PySide.QtGui import *
from PySide.QtCore import Qt, QSize
from PySide.QtDeclarative import QDeclarativeView
from PySide.QtUiTools import QUiLoader

from austro.asm import assembler
from austro.simulator.cpu import CPU
from austro.ui.codeeditor import CodeEditor, AssemblyHighlighter
from austro.ui.models import DataModel, RegistersModel, MemoryModel


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
        leftsplitter.setStretchFactor(0, 5)
        leftsplitter.setStretchFactor(1, 2)
        leftsplitter.setStretchFactor(2, 2)

        middlesplitter = gui.findChild(QSplitter, "middlesplitter")
        middlesplitter.setStretchFactor(0, 2)
        middlesplitter.setStretchFactor(1, 1)

        # Models
        self.genRegsModel = RegistersModel(cpu.registers, (
                'AX', ('AH', 'AL'), 'BX', ('BH', 'BL'),
                'CX', ('CH', 'CL'), 'DX', ('DH', 'DL'),
                'SP', 'BP', 'SI', 'DI',
            ))
        self.specRegsModel = RegistersModel(cpu.registers, (
                'PC', 'RI', 'MAR', 'MBR',
            ))
        self.stateRegsModel = RegistersModel(cpu.registers, (
                'N', 'Z', 'V', 'T',
            ))
        self.memoryModel = MemoryModel(cpu.memory)

        # Get trees
        treeGenericRegs = gui.findChild(QTreeView, "treeGenericRegs")
        treeGenericRegs.setModel(self.genRegsModel)
        treeGenericRegs.expandAll()
        treeGenericRegs.resizeColumnToContents(0)
        treeGenericRegs.resizeColumnToContents(1)

        treeSpecificRegs = gui.findChild(QTreeView, "treeSpecificRegs")
        treeSpecificRegs.setModel(self.specRegsModel)
        treeSpecificRegs.expandAll()
        treeSpecificRegs.resizeColumnToContents(0)
        treeSpecificRegs.resizeColumnToContents(1)

        treeStateRegs = gui.findChild(QTreeView, "treeStateRegs")
        treeStateRegs.setModel(self.stateRegsModel)
        treeStateRegs.expandAll()
        treeStateRegs.resizeColumnToContents(0)
        treeStateRegs.resizeColumnToContents(1)

        tblMemory = gui.findChild(QTableView, "tblMemory")
        tblMemory.setModel(self.memoryModel)
        tblMemory.resizeColumnToContents(0)

        #
        ## Actions
        #
        self.actionLoad = gui.findChild(QAction, "actionLoad")
        self.actionLoad.triggered.connect(self.loadAssembly)

        self.actionRun = gui.findChild(QAction, "actionRun")
        self.actionRun.triggered.connect(self.runAction)

        self.actionStep = gui.findChild(QAction, "actionStep")

        self.actionStop = gui.findChild(QAction, "actionStop")
        self.actionStop.triggered.connect(self.stopAction)

    def loadAssembly(self):
        editor = self.asmEdit
        assembly = editor.toPlainText()
        asmd = assembler.assemble(assembly)

        self.cpu.reset()
        self.cpu.set_memory_block(asmd['words'])
        self.refreshModels()

        self.actionLoad.setEnabled(False)
        self.actionRun.setEnabled(True)
        self.actionStep.setEnabled(True)
        self.actionStop.setEnabled(True)

    def runAction(self):
        self.cpu.start()
        self.refreshModels()

    def stopAction(self):
        self.actionLoad.setEnabled(True)
        self.actionRun.setEnabled(False)
        self.actionStep.setEnabled(False)
        self.actionStop.setEnabled(False)

    def refreshModels(self):
        self.genRegsModel.refresh()
        self.specRegsModel.refresh()
        self.stateRegsModel.refresh()
        self.memoryModel.refresh()

    def show(self):
        self.gui.show()
