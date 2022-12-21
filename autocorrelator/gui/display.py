import numpy as np
import pyqtgraph as pg
from PyQt5 import QtWidgets, QtCore, QtGui


# TODO : show intensity number and more basic qt label based on autoalign
class Display(pg.GraphicsLayoutWidget):
    
    class Signal(QtCore.QObject):
        resize = QtCore.pyqtSignal()
        update = QtCore.pyqtSignal()
        close  = QtCore.pyqtSignal()

    signal = Signal()
        
    __title  = "Autocorrelator - Display"

    def __init__(self, parent=None):
        ''' Displays autocorrelator data.
        '''
        super().__init__()
        self.parent = parent

        self.setupUI()
        self.setupSignals()
        self.activateWindow()
        self.show()

    def setupUI(self):
        self.setWindowTitle(self.__title)
        self.resize(1200, 400)
        screen = QtGui.QGuiApplication.primaryScreen().geometry()
        self.move(0,int(0.25*screen.height()))
            
        # Add empty plot
        plot = self.addPlot(row=0, col=0)
        self.plot = plot.plot() # Initializes plot so it can be updated later

    def setupSignals(self):
        ''' Connects signals to slots. '''
        pass

    def setIntensityPlot(self, intensity_data, x_axis=None):
        ''' Sets the average intensity plot. 

            INPUT :
                intensity_data = 1D array containing the sensor intensity readings acquired so far in the scan.
                x_axis = 1D array containing the delay positions (mm) or delay time (fs) to associate with each delay position in the scan (deault is None)
        '''
        if x_axis:
            self.plot.setData(y=intensity_data, x=x_axis)
        else:
            self.plot.setData(intensity_data)

    def closeEvent(self, event):
        self.signal.close.emit()
        event.accept()

        

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    display_panel = Display()
    display_panel.setIntensityPlot(np.random.randn(100))
    app.exec_()
