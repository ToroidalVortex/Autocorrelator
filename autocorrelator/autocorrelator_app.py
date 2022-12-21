import os
import sys
import time
import traceback
from threading import Thread

import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui

from gui.gui import AutocorrelatorGUI
from delay_controller import DelayStageController
from analog_input import AnalogInput

try:
    import mcc
    mcc_loaded = True
    print('MCC loaded properly')
except:
    mcc_loaded = False
    print('MCC failed to load')

class Autocorrelator:
    def __init__(self):
        ''' Autocorrelator application. 

        Usage:  Autocorrelator = Autocorrelator()
        
        '''
        self.path = os.path.dirname(os.path.abspath(__file__))
        self.app = QtWidgets.QApplication(sys.argv)
        self.gui = AutocorrelatorGUI()
        self.settings = self.gui.getSettings()        
        self.acquiring = False

        self.delay_stage_serial_port = 'COM5'
        self.delay_stage = DelayStageController(self.delay_stage_serial_port)

        self.sensor_channel = 'Dev1/ai2'
        self.sample_rate = 1000

        self.zero_position = 0.000
        self.intensities = []

        if mcc_loaded:
            self.mcc_model = '3101'
            self.MCC = mcc.MCCDev(model=self.mcc_model)
            self.shutter = 1 # pump shutter channel
            # self.shutter = 2 # stokes shutter channel
            self.close_shutter()
        
        self.setup_signals()
        sys.exit(self.app.exec_())

    
    def __del__(self):
        self.close_shutter()
        self.sensor.clear()

    def setup_signals(self):
        self.gui.ui.acquireButton.clicked.connect(self.acquire_toggle)
        self.gui.signal.update.connect(self.update)
        self.gui.signal.close.connect(self.gui_closed)

        # shutter control
        self.gui.ui.shutterButton.clicked.connect(self.toggle_shutter)

        # Delay stage position button
        self.gui.ui.delaySelectButton.clicked.connect(lambda: self.delay_stage.set_position(self.gui.ui.delaySelectWidget.value()))

        # Change zero poisition
        self.gui.ui.delayZeroButton.clicked.connect(lambda: self.set_zero_position(self.gui.ui.delayZeroWidget.value()))


    def update(self):
        ''' Update config based on gui settings. '''
        # Update settings
        self.settings = self.gui.getSettings()

        # Update estimated scan times
        scan_time = self.get_scan_time(self.settings['scan start'], self.settings['scan end'], self.settings['scan step'], self.settings['samples'])
        self.gui.ui.estimatedScanTimeLabel.setText(f'Estimated Scan Time: {scan_time} seconds')

        # Update current delay stage position
        delay_position = self.delay_stage.get_position()
        self.gui.ui.delayStagePosition.setText(f'{delay_position:.3f} mm ({self.delay_to_femto(delay_position):.0f} fs)')

        # Update selected delay stage position femtoseconds calculations
        self.gui.ui.delaySelectFemto.setText(f'{self.delay_to_femto(self.gui.ui.delaySelectWidget.value()):.0f} fs')

        # Update scan values femtoseconds calculations
        self.gui.ui.scanStartFemto.setText(f'{self.delay_to_femto(self.gui.ui.scanStartWidget.value()):.0f} fs')
        self.gui.ui.scanEndFemto.setText(f'{self.delay_to_femto(self.gui.ui.scanEndWidget.value()):.0f} fs')
        self.gui.ui.scanStepFemto.setText(f'{self.gui.ui.scanStepWidget.value()/0.000299792:.0f} fs')

    def gui_closed(self):
        # Stop everything
        self.acquiring = False
        # self.app.quit()

    def save_settings(fname, settings):
        with open(fname, 'w') as file:
            for key, value in settings.items():
                file.write(f'{key} = {value}\n')

    def delay_to_femto(self, delay_position):
        c = 0.000299792 # mm/fs
        return (delay_position - self.zero_position)/c

    def set_zero_position(self, position):
        self.zero_position = position

    def get_scan_time(self, start, stop, step, samples_per_point, time_per_sample=0.001):
        return ((stop-start)/step+1)*samples_per_point*time_per_sample

    def open_shutter(self):
        if mcc_loaded:
            self.MCC.set_digital_out(0, self.shutter)
            self.shutter_open = True
            self.gui.ui.shutterStatusLabel.setText('Open')

    def close_shutter(self):
        if mcc_loaded:
            self.MCC.set_digital_out(1, self.shutter)
            self.shutter_open = False
            self.gui.ui.shutterStatusLabel.setText('Closed')

    def toggle_shutter(self):
        if self.shutter_open:
            self.close_shutter()
        else:
            self.open_shutter()

    def acquire_toggle(self):
        if not self.acquiring:
            self.acquire()
        elif self.acquiring:
            self.stop_acquire()

    def acquire(self):
        self.acquiring = True
        self.gui.ui.acquireButton.setText('Stop')
        if self.gui.display is None:
                self.gui.createDisplayPanel()
        
        self.settings = self.gui.getSettings()

        if self.settings['save']:
            # Create save directory
            self.save_time = time.strftime("%Y_%m_%d_%H%M%S", time.gmtime())
            self.save_directory = f"{self.settings['directory']}/{self.settings['filename']}_{self.save_time}"
            os.mkdir(self.save_directory)
            
            # Save settings
            self.save_settings(f'{self.save_directory}/settings.txt', self.settings)

            # Create csv for average intensities
            np.savetxt(f'{self.save_directory}/intensities.csv', [], delimiter=',', header='delay (mm), intensity (V)')
        
        scan_mode = self.settings['scan mode']

        if scan_mode == 'Scan':
            scan_thread = Thread(target=self.acquire_scan)
            scan_thread.deamon = True
            scan_thread.start()
        
        elif scan_mode == 'Monitor':
            monitor_thread = Thread(target=self.acquire_monitor)
            monitor_thread.deamon = True
            monitor_thread.start()
            

    def acquire_scan(self):
        print('Scanning...')
        self.intensities = []
        self.sensor = AnalogInput(self.sensor_channel, clock_rate=self.sample_rate, mode='continuous')
        # Calculate scan points
        start = self.settings['scan start']
        end   = self.settings['scan end']
        step  = self.settings['scan step']
        samples = int(self.settings['samples'])
        if end < start:
            step = -1*step
        delay_positions = np.arange(start, end+step, step)
        ### initiate scan
        for position in delay_positions:
            try:
                self.delay_stage.set_position(position)
                data = self.sensor.read(samples_per_channel=samples)
                intensity = np.mean(data)
                self.intensities.append(intensity)
                self.gui.updateIntensityPlot(self.intensities)
                if self.settings['save']:
                    with open(f'{self.save_directory}/intensities.csv', 'a') as file:
                        # append intensity to csv
                        np.savetxt(file, [position, intensity], delimiter=',')
                if not self.acquiring: break
            except:
                break
        self.sensor.stop()
        self.sensor.clear()
        self.stop_acquire()
        print('scan finished')

    def acquire_monitor(self):
        print('Monitoring...')
        self.intensities = []
        self.sensor = AnalogInput(self.sensor_channel, clock_rate=self.sample_rate, mode='continuous')
        samples = int(self.settings['samples'])
        while self.acquiring:
            try:
                data = self.sensor.read(samples_per_channel=samples)
                intensity = np.mean(data)
                self.intensities.append(intensity)
                self.gui.updateIntensityPlot(self.intensities)
                if self.settings['save']:
                    with open(f'{self.save_directory}/intensities.csv', 'a') as file:
                        # append intensity to csv
                        np.savetxt(file, [self.delay_stage.get_position(), intensity], delimiter=',')
            except KeyboardInterrupt:
                break
        self.sensor.stop()
        self.sensor.clear()
        self.stop_acquire()
        print('Finished monitoring.')
            
    def stop_acquire(self):
        self.acquiring = False
        self.gui.ui.acquireButton.setText('Acquire')

    def clear_data(self):
        self.intensities = []

def handle_exception(exc_type, exc_value, exc_traceback):
        ''' Prints error that crashed application. '''
        print("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        sys.exit(1)

def main():
    sys.excepthook = handle_exception
    
    ############ Code required for custom application icon in taskbar ############
    import ctypes
    import os
    myappid = u'Autocorrelator'  # arbitrary string
    if os.name == "nt":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    ##############################################################################
    
    autocorrelator = Autocorrelator()

if __name__ == '__main__':
    main()