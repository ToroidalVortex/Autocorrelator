from zaber_motion import Units, Library
from zaber_motion.binary import Connection

Library.enable_device_db_store() # stores retrieved device info in local database

class DelayStageController:
    ''' Preferred usage with context manager (i.e. "with Connection.open_serial_port("COM5") as connection") so that connection properly closes. '''
    def __init__(self, serial_port):
        self.serial_port = serial_port
        self.connection = Connection.open_serial_port(serial_port)
        self.device = self.connection.detect_devices()[0]
        self.units = Units.LENGTH_MILLIMETRES

    def __del__(self):
        if self.connection:
            self.connection.close()
        print('Delay stage connection closed.')

    def get_position(self):
        return self.device.get_position(self.units)

    def set_position(self, position):
        self.device.move_absolute(position, self.units)

    def home(self):
        self.device.home()


if __name__ == '__main__':

    print('Connecting to device.')
    device = DelayStageController('COM5')
    print(f'Device settings: {device.settings()}')

    print('Going home.')
    device.home()

    import time

    print(f'Current Position: {device.get_position()} mm')

    pos = 10
    print(f'Moving to {pos} mm')
    device.set_position(pos)

    print(f'Current Position: {device.get_position()} mm')

    print('Done.')
