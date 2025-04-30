# Copyright (C) 2013  Wagner Macedo <wagnerluis1982@gmail.com>
#
# This file is part of Austro Simulator.
#
# Austro Simulator is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Austro Simulator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Austro Simulator.  If not, see <http://www.gnu.org/licenses/>.

#
## The code here was vastly based on Qt Tutorials. See: <http://qt-project.org>
#

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from austro.asm.assembler import OPCODES, REGISTERS


class CodeEditor(QPlainTextEdit):
    lineNumberArea = None

    def __init__(self, parent=None):
        super(CodeEditor, self).__init__(parent)
        self.setTabStopWidth(40)
        self.lineNumberArea = LineNumberArea(self)

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

        self.defaultPalette = self.palette()
        self.readOnlyPalette = self.palette()
        self.readOnlyPalette.setColor(QPalette.Active, QPalette.Base,
                QColor("#F4F4F4"))

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), self.palette().color(QPalette.Window))
        painter.setPen(Qt.black)

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber() + 1
        top = self.blockBoundingGeometry(block)\
                .translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        areaWidth = self.lineNumberArea.width()
        rightMargin = self.lineNumberArea.RIGHT_MARGIN

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber)
                painter.drawText(0, top, areaWidth - rightMargin,
                        self.fontMetrics().height(), Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1

    def lineNumberAreaWidth(self):
        digits = 1
        maxdigs = max(1, self.blockCount())
        while maxdigs >= 10:
            maxdigs //= 10
            digits += 1

        space = 3 + self.fontMetrics().width('9') * digits
        rightMargin = self.lineNumberArea.RIGHT_MARGIN

        return space + rightMargin

    def resizeEvent(self, e):
        QPlainTextEdit.resizeEvent(self, e)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(),
            self.lineNumberAreaWidth(), cr.height()))

    def updateLineNumberAreaWidth(self, newBlockCount):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def highlightCurrentLine(self, lineColor=QColor("#F8F7F6"), force=False):
        if not self.isReadOnly() or force:
            extraSelections = []

            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)

            self.setExtraSelections(extraSelections)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(),
                    self.lineNumberArea.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def setReadOnly(self, enable=True):
        super(CodeEditor, self).setReadOnly(enable)

        if enable:
            self.highlightCurrentLine(Qt.transparent, force=True)
            self.deselect()
            self.setPalette(self.readOnlyPalette)
        else:
            self.highlightCurrentLine()
            self.setPalette(self.defaultPalette)

    def highlightLine(self, lineNo, lineColor=QColor("#C6DBAE")):
        if lineNo > 0:
            block = self.document().findBlockByLineNumber(lineNo-1)
            cursor = self.textCursor()
            cursor.setPosition(block.position())
            cursor.clearSelection()
            self.setTextCursor(cursor)

            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = cursor

            extraSelections = [selection]
            self.setExtraSelections(extraSelections)
        else:
            self.highlightCurrentLine(Qt.transparent, force=True)

    def deselect(self):
        self.moveCursor(QTextCursor.End)
        self.moveCursor(QTextCursor.Left)


class LineNumberArea(QWidget):
    RIGHT_MARGIN = 3
    codeEditor = None

    def __init__(self, editor):
        super(LineNumberArea, self).__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)


class HighlightingRule(object):
    pattern = None
    format = None


class AssemblyHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super(AssemblyHighlighter, self).__init__(parent)

        self.highlightingRules = []
        self.opcodeFormat = QTextCharFormat()
        self.registerFormat = QTextCharFormat()

        self.opcodeFormat.setForeground(Qt.darkBlue)
        self.opcodeFormat.setFontWeight(QFont.Bold)
        opcodePatterns = OPCODES.keys()
        for pattern in opcodePatterns:
            rule = HighlightingRule()
            rule.pattern = QRegExp(r'\b%s\b' % pattern, Qt.CaseInsensitive)
            rule.format = self.opcodeFormat
            self.highlightingRules.append(rule)

        self.registerFormat.setForeground(Qt.darkMagenta)
        self.registerFormat.setFontWeight(QFont.Bold)
        registerPatterns = REGISTERS.keys()
        for pattern in registerPatterns:
            rule = HighlightingRule()
            rule.pattern = QRegExp(r'\b%s\b' % pattern, Qt.CaseInsensitive)
            rule.format = self.registerFormat
            self.highlightingRules.append(rule)

    def highlightBlock(self, text):
        for rule in self.highlightingRules:
            expression = QRegExp(rule.pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, rule.format)
                index = expression.indexIn(text, index + length)
