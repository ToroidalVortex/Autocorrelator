from PyQt5 import QtCore, QtWidgets, QtGui

from .autocorrelator_ui import Ui_MainWindow
from .display import Display


class AutocorrelatorGUI(QtWidgets.QMainWindow):

    class Signal(QtCore.QObject):
        acquire = QtCore.pyqtSignal()
        stop = QtCore.pyqtSignal()
        update = QtCore.pyqtSignal()
        close = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.signal = self.Signal()
        self.display = Display(parent=self)
        self.acquiring = False
        self.setupUI()
        self.setupSignals()
        
    def setupUI(self):
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Autocorrelator")
        # self.setWindowIcon(QtGui.QIcon('autocorrelator/gui/icon.png'))
        screen = QtGui.QGuiApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move(1200, int(0.25*screen.height()))
        self.activateWindow()
        self.show()

    def setupSignals(self):
        self.ui.directoryBrowseButton.clicked.connect(lambda: self.ui.directoryText.setText(QtWidgets.QFileDialog.getExistingDirectory()))
        self.display.signal.close.connect(self.displayClosed)

        # Update timer to periodically emit update signal
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(False)
        self.timer.setInterval(500) # in milliseconds
        self.timer.timeout.connect(lambda: self.signal.update.emit())
        self.timer.start()

    def displayClosed(self):
        self.display = None
        
    def createDisplayPanel(self):
        self.display = Display(parent=self)

    def updateIntensityPlot(self, intensity_data, x_axis=None):
        self.display.setIntensityPlot(intensity_data, x_axis)
    
    def getSettings(self):
        settings = {}
        settings['scan mode'] = self.ui.scanModeWidget.currentText()
        settings['filename'] = self.ui.filenameText.text()
        settings['directory'] = self.ui.directoryText.text()
        settings['save'] = self.ui.saveCheckBox.isChecked()
        settings['scan start'] = self.ui.scanStartWidget.value()
        settings['scan end'] = self.ui.scanEndWidget.value()
        settings['scan step'] = self.ui.scanStepWidget.value()
        settings['samples'] = self.ui.scanSamplesWidget.value()
        settings['zero position'] = self.ui.delayZeroWidget.value()
        return settings

    def closeEvent(self, event):
        # close all windows
        self.signal.close.emit()
        self.display.close()
        event.accept()

if __name__ == '__main__':
    import sys
    import numpy as np
    app = QtWidgets.QApplication(sys.argv)
    gui = AutocorrelatorGUI()
    gui.updateIntensityPlot(np.random.randn(100))
    exit(app.exec_())