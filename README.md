GUI program used for controlling the interferometric autocorrelator the lab uses to measure ultrashort laser pulses from the pump beam.

Hardware requirements:
- Zaber - Linear Stage: for optical delay scanning.
- National Instruments - PCI DAQ: for acquiring intensity from optical sensor. 

Software requirements:
- USB drivers for hardware.
- Python packages in `requirements.txt`

How to use:
- Run `autocorrelator_app.py` to launch the GUI application.
- Input your preferred settings.
- Click `Acquire`.