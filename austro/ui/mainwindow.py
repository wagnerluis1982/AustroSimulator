import os

from PySide.QtGui import *
from PySide.QtCore import Qt, QThread
from PySide.QtDeclarative import QDeclarativeView
from PySide.QtUiTools import QUiLoader

from austro.asm import assembler
from austro.simulator.cpu import CPU, Stage, StepEvent
from austro.ui.codeeditor import CodeEditor, AssemblyHighlighter
from austro.ui.models import DataModel, RegistersModel, MemoryModel


def _resource(*rsc):
    directory = os.path.dirname(__file__).decode("utf8")
    return os.path.join(directory, *rsc)


class ModelsUpdater(StepEvent):
    def __init__(self, win):
        self.win = win

    def on_fetch(self):
        # Highlight current execution line
        lineno = self.cpu.registers.get_word('RI').lineno
        self.win.asmEdit.highlightLine(lineno)

        # Highlight current memory position
        self.win.memoryModel.pc = self.cpu.registers['PC']
        self.win.refreshModels()
        # Ensure memory position is visible
        index = self.win.memoryModel.index(self.cpu.registers['PC'], 0)
        self.win.treeMemory.scrollTo(index)


class MainWindow(object):
    def __init__(self, qApp=None):
        self.event = ModelsUpdater(self)
        self.cpu = CPU(self.event)
        self.emitter = None

        qApp.lastWindowClosed.connect(self.stopAndWait)

        loader = QUiLoader()
        loader.registerCustomWidget(CodeEditor)
        self.gui = loader.load(_resource('mainwindow.ui'))

        self.setupEditorAndDiagram()
        self.setupSplitters()
        self.setupModels()
        self.setupTrees()
        self.setupActions()

    def setupEditorAndDiagram(self):
        # Assembly editor get focus on start
        self.asmEdit = self.gui.findChild(CodeEditor, "asmEdit")
        self.asmEdit.setFocus()
        AssemblyHighlighter(self.asmEdit.document())

        # Set QML file
        cpuDiagram = self.gui.findChild(QDeclarativeView, "cpuDiagram")
        cpuDiagram.setSource(_resource('qml', 'computer.qml'))

    #
    ## Define size factor for each splitted region.
    #
    def setupSplitters(self):
        mainsplitter = self.gui.findChild(QSplitter, "mainsplitter")
        mainsplitter.setStretchFactor(0, 3)
        mainsplitter.setStretchFactor(1, 8)
        mainsplitter.setStretchFactor(2, 3)

        leftsplitter = self.gui.findChild(QSplitter, "leftsplitter")
        leftsplitter.setStretchFactor(0, 5)
        leftsplitter.setStretchFactor(1, 2)
        leftsplitter.setStretchFactor(2, 2)

        middlesplitter = self.gui.findChild(QSplitter, "middlesplitter")
        middlesplitter.setStretchFactor(0, 2)
        middlesplitter.setStretchFactor(1, 1)

    #
    ## Models
    #
    def setupModels(self):
        self.genRegsModel = RegistersModel(self.cpu.registers, (
                'AX', ('AH', 'AL'), 'BX', ('BH', 'BL'),
                'CX', ('CH', 'CL'), 'DX', ('DH', 'DL'),
                'SP', 'BP', 'SI', 'DI',
            ))
        self.specRegsModel = RegistersModel(self.cpu.registers, (
                'PC', 'RI', 'MAR', 'MBR',
            ))
        self.stateRegsModel = RegistersModel(self.cpu.registers, (
                'N', 'Z', 'V', 'T',
            ))
        self.memoryModel = MemoryModel(self.cpu.memory)

    #
    ## Get trees
    #
    def setupTrees(self):
        treeGenericRegs = self.gui.findChild(QTreeView, "treeGenericRegs")
        treeGenericRegs.setModel(self.genRegsModel)
        treeGenericRegs.expandAll()
        treeGenericRegs.resizeColumnToContents(0)
        treeGenericRegs.resizeColumnToContents(1)

        treeSpecificRegs = self.gui.findChild(QTreeView, "treeSpecificRegs")
        treeSpecificRegs.setModel(self.specRegsModel)
        treeSpecificRegs.expandAll()
        treeSpecificRegs.resizeColumnToContents(0)
        treeSpecificRegs.resizeColumnToContents(1)

        treeStateRegs = self.gui.findChild(QTreeView, "treeStateRegs")
        treeStateRegs.setModel(self.stateRegsModel)
        treeStateRegs.expandAll()
        treeStateRegs.resizeColumnToContents(0)
        treeStateRegs.resizeColumnToContents(1)

        self.treeMemory = self.gui.findChild(QTreeView, "treeMemory")
        treeMemory = self.treeMemory
        treeMemory.setModel(self.memoryModel)
        treeMemory.resizeColumnToContents(0)
        treeMemory.resizeColumnToContents(1)

        #
        ## Add a context menu to tree headers to select data format
        self.dataContextMenu = QMenu()
        menu = self.dataContextMenu
        decAction = menu.addAction("Decimal")
        decAction.setData(DataModel.F_DEC)
        negAction = menu.addAction("Negative (2's complement)")
        negAction.setData(DataModel.F_DEC_NEG)
        binAction = menu.addAction("Binary")
        binAction.setData(DataModel.F_BIN)
        octAction = menu.addAction("Octal")
        octAction.setData(DataModel.F_OCT)
        hexAction = menu.addAction("Hexadecimal")
        hexAction.setData(DataModel.F_HEX)

        treeGenericRegs.header().setContextMenuPolicy(Qt.CustomContextMenu)
        treeGenericRegs.header().customContextMenuRequested.connect(
                lambda pos: self.headerMenu(pos, treeGenericRegs))

        treeSpecificRegs.header().setContextMenuPolicy(Qt.CustomContextMenu)
        treeSpecificRegs.header().customContextMenuRequested.connect(
                lambda pos: self.headerMenu(pos, treeSpecificRegs))

        treeStateRegs.header().setContextMenuPolicy(Qt.CustomContextMenu)
        treeStateRegs.header().customContextMenuRequested.connect(
                lambda pos: self.headerMenu(pos, treeStateRegs))

        treeMemory.header().setContextMenuPolicy(Qt.CustomContextMenu)
        treeMemory.header().customContextMenuRequested.connect(
                lambda pos: self.headerMenu(pos, treeMemory))

    #
    ## Actions
    #
    def setupActions(self):
        self.actionLoad = self.gui.findChild(QAction, "actionLoad")
        self.actionLoad.triggered.connect(self.loadAssembly)

        self.actionRun = self.gui.findChild(QAction, "actionRun")
        self.actionRun.triggered.connect(self.runAction)

        self.actionStep = self.gui.findChild(QAction, "actionStep")
        self.actionStep.triggered.connect(self.nextInstruction)

        self.actionStop = self.gui.findChild(QAction, "actionStop")
        self.actionStop.triggered.connect(self.stopAction)

    def loadAssembly(self):
        # Disable editor so will reflect the running program
        editor = self.asmEdit
        editor.setDisabled()

        # Assemble the program
        assembly = editor.toPlainText()
        asmd = assembler.assemble(assembly)

        # Reset and set the memory with the written program
        self.cpu.reset()
        self.cpu.set_memory_block(asmd['words'])
        self.refreshModels()

        # Enable/Disable actions
        self.actionLoad.setEnabled(False)
        self.actionRun.setEnabled(True)
        self.actionStep.setEnabled(True)
        self.actionStop.setEnabled(True)

    def emitStart(self):
        while self.cpu.stage not in (Stage.HALTED, Stage.STOPPED):
            self.cpu.next()
            QThread.msleep(100)

        self.refreshModels()
        self.restoreEditor()

    def runAction(self):
        self.actionRun.setEnabled(False)
        self.actionStep.setEnabled(False)

        self.emitter = Emitter(self.emitStart)
        self.emitter.start()

    def nextInstruction(self):
        self.cpu.next()

        if self.cpu.stage == Stage.HALTED:
            self.restoreEditor()

    def stopAndWait(self):
        # Stop correctly
        self.cpu.stop()
        if self.emitter is not None:
            self.emitter.wait()

    def stopAction(self):
        self.stopAndWait()
        self.restoreEditor()

    def headerMenu(self, pos, tree=None):
        if tree is None:
            return

        column = tree.header().logicalIndexAt(pos)
        if column == 1:
            action = self.dataContextMenu.exec_(tree.mapToGlobal(pos))
            if action:
                tree.model().setDataFormat(action.data())

    def restoreEditor(self):
        # Enable/Disable actions
        self.actionLoad.setEnabled(True)
        self.actionRun.setEnabled(False)
        self.actionStep.setEnabled(False)
        self.actionStop.setEnabled(False)
        # Re-enable editor
        self.asmEdit.setEnabled()
        self.asmEdit.setFocus()
        # Reset MemoryModel internal PC
        self.memoryModel.pc = -1
        self.memoryModel.refresh()

    def refreshModels(self):
        self.genRegsModel.refresh()
        self.specRegsModel.refresh()
        self.stateRegsModel.refresh()
        self.memoryModel.refresh()

    def show(self):
        self.gui.show()


class Emitter(QThread):
    def __init__(self, fn):
        super(Emitter, self).__init__()
        self.fn = fn

    def run(self):
        self.fn()
