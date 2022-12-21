import numpy as np
import matplotlib.pyplot as plt


def sech2(t, duration):
    return 1/np.cosh(1.76*t/duration)**2




if __name__ == '__main__':
    x = np.linspace(-500,500,1000)
    y = sech2(x, 190)
    ac = np.correlate(y, y, 'same')
    
    plt.figure()
    plt.title('Pulse')
    plt.plot(x, y)
    plt.xlabel('Delay (fs)')
    plt.ylabel('Intensity (arb.)')
    plt.show()

    plt.figure()
    plt.plot(x, ac)
    plt.xlabel('Delay (fs)')
    plt.ylabel('Intensity (arb.)')
    plt.legend()
    plt.show()
