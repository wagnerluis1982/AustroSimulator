from __future__ import annotations

import os

from datetime import datetime
from typing import TYPE_CHECKING, override

# from PyQt5.QtWebKit import QWebView
# from PyQt5.QtDeclarative import QDeclarativeView
# from PyQt5.QtUiTools import QUiLoader
from PyQt5 import uic
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QAction,
    QFileDialog,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QSplitter,
    QTreeView,
)

from austro.asm import asm_lexer, assembler
from austro.simulator.cpu import CPU, CPUException, Stage, StepListener
from austro.ui.codeeditor import AssemblyHighlighter, CodeEditor
from austro.ui.models import DataModel, GeneralMemoryModel, MemoryModel, RegistersModel


if TYPE_CHECKING:
    from PyQt5.QtWidgets import QApplication, QMainWindow

    from austro.simulator.cpu import Memory, Registers


__version__ = "0.2.0-alpha2"
_about_ = (
    """
    <h3>Austro Simulator %s</h3>
    <p>Copyright (C) 2013  Wagner Macedo</p>

    <p>
    Austro Simulator is free software: you can redistribute it
    and/or modify it under the terms of the GNU General Public
    License as published by the Free Software Foundation, either
    version 3 of the License, or (at your option) any later version.
    </p>

    <p>
    Austro Simulator is distributed in the hope that it will be
    useful, but WITHOUT ANY WARRANTY; without even the implied
    warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.
    </p>
    """
    % __version__
)


def _resource(*rsc):
    directory = os.path.dirname(__file__)
    return os.path.join(directory, *rsc)


class ModelsUpdater(StepListener):
    def __init__(self, win: MainWindow):
        self.win = win

    @override
    def on_fetch(self, registers: Registers, memory: Memory) -> None:
        # Highlight current execution line
        lineno = registers.get_word("RI").lineno
        self.win.asmEdit.highlightLine(lineno)

        # Highlight current memory position
        self.win.memoryModel.pc = registers["PC"]
        self.win.refreshModels()
        # Ensure memory position is visible
        index = self.win.memoryModel.index(registers["PC"])
        self.win.treeMemory.scrollTo(index)


class MainWindow:
    def __init__(self, qApp: QApplication):
        self.listener = ModelsUpdater(self)
        self.cpu = CPU(self.listener)

        qApp.lastWindowClosed.connect(self.stop)

        # loader = QUiLoader()
        # loader.registerCustomWidget(CodeEditor)
        self.gui: QMainWindow = uic.loadUi(_resource("mainwindow.ui"))

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

        # Get console area
        self.console = self.gui.findChild(QPlainTextEdit, "txtConsole")

        # Set QML file
        # cpuDiagram = self.gui.findChild(QDeclarativeView, "cpuDiagram")
        # cpuDiagram.setSource(_resource('qml', 'computer.qml'))

        # webInstruct = self.gui.findChild(QWebView, "webInstruct")
        # webInstruct.setUrl(_resource('html', 'instructions.html'))

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
        self.genRegsModel = RegistersModel(
            self.cpu.registers,
            (
                "AX",
                ("AH", "AL"),
                "BX",
                ("BH", "BL"),
                "CX",
                ("CH", "CL"),
                "DX",
                ("DH", "DL"),
                "SP",
                "BP",
                "SI",
                "DI",
            ),
        )
        self.specRegsModel = RegistersModel(
            self.cpu.registers,
            (
                "PC",
                "RI",
                "MAR",
                "MBR",
            ),
        )
        self.stateRegsModel = RegistersModel(
            self.cpu.registers,
            (
                "N",
                "Z",
                "V",
                "T",
            ),
        )
        self.memoryModel = GeneralMemoryModel(self.cpu.memory)
        self.memoryModel2 = MemoryModel(self.cpu.memory)

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

        # Main vision tree memory
        self.treeMemory = self.gui.findChild(QTreeView, "treeMemory")
        treeMemory = self.treeMemory
        treeMemory.setModel(self.memoryModel)
        treeMemory.resizeColumnToContents(0)
        treeMemory.resizeColumnToContents(1)

        # Data vision tree memory
        treeMemory2 = self.gui.findChild(QTreeView, "treeMemory2")
        treeMemory2.setModel(self.memoryModel2)
        treeMemory2.resizeColumnToContents(0)
        treeMemory2.resizeColumnToContents(1)
        # Initially scroll to half of memory
        index = self.memoryModel2.index(self.cpu.memory.size // 2)
        treeMemory2.scrollTo(index)

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
            lambda pos: self.headerMenu(pos, treeGenericRegs)
        )

        treeSpecificRegs.header().setContextMenuPolicy(Qt.CustomContextMenu)
        treeSpecificRegs.header().customContextMenuRequested.connect(
            lambda pos: self.headerMenu(pos, treeSpecificRegs)
        )

        treeStateRegs.header().setContextMenuPolicy(Qt.CustomContextMenu)
        treeStateRegs.header().customContextMenuRequested.connect(
            lambda pos: self.headerMenu(pos, treeStateRegs)
        )

        treeMemory2.header().setContextMenuPolicy(Qt.CustomContextMenu)
        treeMemory2.header().customContextMenuRequested.connect(
            lambda pos: self.headerMenu(pos, treeMemory2)
        )

        # Context menu of general memory vision
        contextMenu = QMenu()
        contextMenu.addAction(decAction)
        contextMenu.addAction(negAction)
        contextMenu.addAction(binAction)
        contextMenu.addAction(octAction)
        contextMenu.addAction(hexAction)
        instrAction = contextMenu.addAction("Instruction")
        instrAction.setData(GeneralMemoryModel.F_INSTR)

        treeMemory.header().setContextMenuPolicy(Qt.CustomContextMenu)
        treeMemory.header().customContextMenuRequested.connect(
            lambda pos: self.headerMenu(pos, treeMemory, contextMenu)
        )

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

        self.actionAbout = self.gui.findChild(QAction, "actionAbout")
        self.actionAbout.triggered.connect(self.about)

        self.actionAboutQt = self.gui.findChild(QAction, "actionAboutQt")
        self.actionAboutQt.setIcon(QIcon(_resource("images", "qt-logo.png")))
        self.actionAboutQt.triggered.connect(self.aboutQt)

        self.actionOpen = self.gui.findChild(QAction, "actionOpen")
        self.actionOpen.triggered.connect(self.openAction)

    def loadAssembly(self):
        # Enable/Disable actions
        self.actionLoad.setEnabled(False)
        self.actionRun.setEnabled(True)
        self.actionStep.setEnabled(True)
        self.actionStop.setEnabled(True)

        # Disable editor so will reflect the simulated running program
        editor = self.asmEdit
        editor.setReadOnly()

        try:
            # Assemble the program
            assembly = editor.toPlainText()
            asmd = assembler.assemble(assembly)
        except (asm_lexer.LexerException, assembler.AssembleException) as e:
            self.console.clear()
            self.console.appendPlainText("Attempt to load failed (%s)" % datetime.now())
            self.console.appendPlainText(e.message)
            self.restoreEditor()
        else:
            try:
                # Reset and set the memory with the written program
                self.cpu.reset()
                self.cpu.set_memory_block(asmd["words"])
                self.refreshModels()
            except CPUException as e:
                self.console.appendPlainText("Attempt to load failed (%s)" % datetime.now())
                self.console.appendPlainText(e.message)
                self.restoreEditor()

    def runAction(self):
        self.actionRun.setEnabled(False)
        self.actionStep.setEnabled(False)

        def do_action():
            if self.cpu.stage not in (Stage.HALTED, Stage.STOPPED):
                self.nextInstruction()
                QTimer.singleShot(200, do_action)
            else:
                self.restoreEditor()

        do_action()

    def nextInstruction(self):
        try:
            next(self.cpu)
        except CPUException as e:
            self.console.appendPlainText("Execution failed (%s)" % datetime.now())
            self.console.appendPlainText(e.message)

        if self.cpu.stage in (Stage.HALTED, Stage.STOPPED):
            self.refreshModels()
            self.restoreEditor()

    def stop(self):
        self.cpu.stop()

    def stopAction(self):
        self.stop()
        self.restoreEditor()

    def openAction(self):
        filename = QFileDialog().getOpenFileName(self.gui, "Open File")[0]

        if os.path.exists(filename):
            if self.asmEdit.document().isModified():
                answer = QMessageBox.question(
                    self.gui,
                    "Modified Code",
                    """<b>The current code is modified</b>
                       <p>What do you want to do?</p>""",
                    QMessageBox.Discard | QMessageBox.Cancel,
                    QMessageBox.Cancel,
                )
                if answer == QMessageBox.Cancel:
                    return
            self.asmEdit.setPlainText(open(filename).read())

    def headerMenu(self, pos, tree=None, contextMenu=None):
        if tree is None:
            return

        if contextMenu is None:
            contextMenu = self.dataContextMenu

        column = tree.header().logicalIndexAt(pos)
        if column == 1:
            action = contextMenu.exec_(tree.mapToGlobal(pos))
            if action:
                tree.model().setDataFormat(action.data())

    def restoreEditor(self):
        # Enable/Disable actions
        self.actionLoad.setEnabled(True)
        self.actionRun.setEnabled(False)
        self.actionStep.setEnabled(False)
        self.actionStop.setEnabled(False)
        # Re-enable editor
        self.asmEdit.setReadOnly(False)
        self.asmEdit.setFocus()
        # Reset MemoryModel internal PC
        self.memoryModel.pc = -1
        self.memoryModel.refresh()

    def refreshModels(self):
        self.genRegsModel.refresh()
        self.specRegsModel.refresh()
        self.stateRegsModel.refresh()
        self.memoryModel.refresh()
        self.memoryModel2.refresh()

    def about(self):
        QMessageBox.about(self.gui, "About Austro Simulator", _about_)

    def aboutQt(self):
        QMessageBox.aboutQt(self.gui)

    def show(self):
        self.gui.show()
