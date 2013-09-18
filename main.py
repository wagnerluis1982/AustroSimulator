import sys

from PySide.QtGui import QApplication
from austro.ui.mainwindow import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    win = MainWindow()
    win.show()

    sys.exit(app.exec_())