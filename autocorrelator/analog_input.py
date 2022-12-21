''' Analog Input using the NI BNC-2110 DAQ connected to the NI PCI-6110. 
    NI DAQmx Documentation: https://documentation.help/NI-DAQmx-C-Functions/
    PyDAQmx  Documentation: https://pythonhosted.org/PyDAQmx/
'''
import numpy as np

try:
    import PyDAQmx as pdmx
except:
    print('PyDAQmx import failed.')


class AnalogInput:
    def __init__(self, channel_name, voltage_min=-10., voltage_max=10., clock_rate=5000000, mode='continuous', samples_per_channel=1, source=None, trigger=None, offset=0):
        ''' Maximum clock rate is 5 MHz for analog input channels. Samples per channel should be no more than 1/10 clock rate.
        '''
        assert mode in ['continuous', 'finite']
        self.channel_name = channel_name
        self.number_of_channels = 1
        self.voltage_min = voltage_min
        self.voltage_max = voltage_max
        self.clock_rate = int(clock_rate)
        self.mode = mode
        self.samples_per_channel = int(samples_per_channel)
        self.source = source
        self.trigger = trigger
        self.offset = offset
        self.task_started = False

        self.task = pdmx.Task()
        self.__configure_task()

    def __del__(self):
        self.clear()

    def __configure_task(self):
        self.task.CreateAIVoltageChan(
            physicalChannel=self.channel_name, 
            nameToAssignToChannel='',
            terminalConfig=pdmx.DAQmx_Val_Cfg_Default,
            minVal=self.voltage_min,
            maxVal=self.voltage_max,
            units=pdmx.DAQmx_Val_Volts,
            customScaleName=None
        )

        if self.mode == 'continuous':
            sample_mode = pdmx.DAQmx_Val_ContSamps
        elif self.mode == 'finite':
            sample_mode = pdmx.DAQmx_Val_FiniteSamps

        self.task.CfgSampClkTiming(
            source=self.source,
            rate=self.clock_rate,
            activeEdge=pdmx.DAQmx_Val_Falling,
            sampleMode=sample_mode,
            sampsPerChan=self.samples_per_channel
        )

        # Sets read offset in samples. This removes the extra sample that was being read before the analog output started.
        offset = pdmx.int32(self.offset)
        pdmx.DAQmxSetReadOffset(self.task.taskHandle, offset)
        # pdmx.DAQmxGetReadOffset(self.task.taskHandle, pdmx.byref(offset))
        # print(f'Read offset: {offset}')
        
        if self.trigger:
            self.task.CfgDigEdgeStartTrig(triggerSource=self.trigger, triggerEdge=pdmx.DAQmx_Val_Rising)


    def read(self, samples_per_channel=None, timeout=10):
        ''' Reads analog input according to the configured task. 

            Inputs : 
                samples_per_channel (int): the number of samples to be read.
                timeout (float): time to wait before stopping task. 

            Returns :
                read_data: 1D numpy array containing read data
        '''
        if not samples_per_channel:
            samples_per_channel = self.samples_per_channel
        else:
            samples_per_channel = int(samples_per_channel)

        self.start()

        read_array = np.zeros(samples_per_channel, dtype=np.float64)
        self.task.ReadAnalogF64(
            numSampsPerChan=samples_per_channel,
            timeout=timeout,
            fillMode=pdmx.DAQmx_Val_GroupByChannel,
            readArray=read_array,
            arraySizeInSamps=samples_per_channel,
            sampsPerChanRead=None,
            reserved=None
        )
        return read_array

    def start(self):
        ''' Preferred way to start the task. '''
        if not self.task_started:
            self.task.StartTask()
            self.task_started = True

    def wait(self, timeout=10.):
        ''' Waits for the task to finish. If the task takes longer than timeout (seconds) it is terminated. '''
        self.task.WaitUntilTaskDone(timeout)

    def stop(self):
        ''' Preferred way to stop the task. '''
        if self.task_started:
            self.task.StopTask()
            self.task_started = False

    def clear(self):
        ''' Preferred way to clear the task. '''
        if self.task: self.task.ClearTask()
        self.task = None
        self.task_started = False


if __name__ == '__main__':
    import time
    import matplotlib.pyplot as plt

    def test_analog_input():
        ''' Testing ananlog input from function generator
            Instructions: Connect function generator output (1 kHz sine wave) to Dev1/ai3.
        '''

        clock_rate = 1000 # samples per second
        number_of_samples = 5000 # samples

        print(f'Read time: {number_of_samples/clock_rate} seconds')

        ai = AnalogInput('Dev1/ai0', clock_rate=clock_rate, mode='finite')
        data = ai.read(samples_per_channel=number_of_samples)
        ai.clear()

        plt.figure()
        plt.plot(data)
        plt.show()

    def test_on_demand_sampling():
        clock_rate = 1000 # samples per second
        number_of_samples = 5000 # samples
        data = []
        ai = AnalogInput('Dev1/ai3', clock_rate=clock_rate, mode='continuous')
        for _ in range(number_of_samples):
            tmp = ai.read(samples_per_channel=1)
            data.append(tmp[0])
        ai.stop()
        ai.clear()

        plt.figure()
        plt.plot(data)
        plt.show()

    def benchmark_read_speed():
        ''' Benchmarking read speed for 62500 samples
        '''

        number_of_samples = 62500

        ai = AnalogInput('Dev1/ai3', clock_rate=5000000, mode='finite')
        ai.start()

        start_time = time.perf_counter()
        ai.read(samples_per_channel=number_of_samples)
        end_time = time.perf_counter()
        
        ai.clear()

        print(f'Time: {end_time - start_time}')


    # test_analog_input()
    test_on_demand_sampling()
    # benchmark_read_speed()

