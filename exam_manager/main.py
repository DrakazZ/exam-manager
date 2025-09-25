import sys
from PyQt5.QtWidgets import QApplication
 
#local imports
from .ui import StudentQRApp


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = StudentQRApp()
    w.show()
    sys.exit(app.exec_())