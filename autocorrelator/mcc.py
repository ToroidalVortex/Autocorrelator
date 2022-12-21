import math

from mcculw import ul
from mcculw.enums import ULRange, DigitalPortType, DigitalIODirection


model_specs = {

    ### Model USB-1208FS specs
    '1208': {
        'channels' : 2,                 # 2 analog output channels
        'resolution' : 12,              # 12-bit resolution
        'range' : ULRange.UNI4VOLTS,    # 0V to 4V voltage range
        'port type': DigitalPortType.FIRSTPORTA,
        'max voltage': 4
    },


    ### Model 3101 specs
    '3101' : {
        'channels' : 4,                 # 4 analog output channels
        'resolution' : 16,              # 16-bit resolution
        'range' : ULRange.UNI10VOLTS,   # 0V to 10V voltage range
        'port type': DigitalPortType.AUXPORT,
        'max voltage': 10
    }

}


class MCCDev:
    ''' Provides computer control over the Measurement Computing USB-1208FS and USB-3101.

        --- USB-1208FS ---
        https://www.mccdaq.com/usb-data-acquisition/USB-1208FS.aspx
        https://www.mccdaq.com/pdfs/manuals/USB-1208FS.pdf

        --- USB-3101 ---
        https://www.mccdaq.com/pdfs/manuals/USB-3101.pdf 

    '''
    def __init__(self, model='3101', board_number=0):
        self.model = model
        self.board_num = board_number
        self.number_of_channels = model_specs[model]['channels']
        self.resolution = model_specs[model]['resolution']
        self.range = model_specs[model]['range']
        self.port_type = model_specs[model]['port type']

    def set_analog_out(self, voltage, channel):
        ''' Sets analog output channel voltage. Voltage must be in the ULRange specified for the given device model. '''
        assert channel in range(self.number_of_channels), 'Invalid channel number.'
        ul.v_out(self.board_num, channel, self.range, voltage)

    def set_digital_out(self, value, port):
        ul.d_config_port(self.board_num, self.port_type, DigitalIODirection.OUT)
        ul.d_bit_out(self.board_num, port_type=self.port_type, bit_num=port, bit_value=value)