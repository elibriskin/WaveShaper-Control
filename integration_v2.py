import pyvisa
import sympy as sp
import matplotlib.pyplot as plt
import numpy as np
# from sympy.abc import x
from sympy.utilities.lambdify import implemented_function
from sympy import lambdify, exp, cos, sin, log, ln
from scipy.integrate import quad
from WaveShaper import WaveShaper

x = sp.Symbol('x')
a = 1
#Initial dispersion function
def dispersion(x):
    return a*(x**0)
# First integration
def first_integral(x):
    return quad(dispersion, 0, x)[0]

first_integral = np.vectorize(first_integral)
def second_integral(x):
    integral = quad(lambda x: quad(dispersion, 0, x)[0], 0, x)[0]
    return integral

second_integral_func = np.vectorize(second_integral)

#Initialize WaveShaper
waveshaper = WaveShaper(device_frequency=False)

#Define start and end wavelengths
start_wavelength = 1.490e-6
end_wavelength = 1.6e-6

#Define center wavelength
# center_wavelength = (start_wavelength + end_wavelength) / 2
center_wavelength = 1.52e-6


#Create wavelength frequencies
waveshaper.start_frequency = waveshaper.get_frequency(end_wavelength)
waveshaper.end_frequency = waveshaper.get_frequency(start_wavelength)
bandwidth = 10e-9 #nm

#Define profile arrays
wsFreq = waveshaper.get_array()
wsAttn = waveshaper.band_pass(center_wavelength, bandwidth)
wsPhase = np.zeros(wsFreq.shape)
wsPort = np.ones(wsFreq.shape)

#The central frequency corresponds to the center frequency within the bandpass region
central_frequency = (np.max(wsFreq[wsAttn==0]) + np.min(wsFreq[wsAttn==0])) / 2

#The phase pattern corresponds to the region of the phase array corresponding to the band pass region
wsPhasePattern = np.linspace(-central_frequency, central_frequency, len(wsFreq[wsAttn==0]))

#Dispersion will only be introduced in the band pass region of the phase array
wsPhaseDispersion = (second_integral_func(wsPhasePattern) / np.max(second_integral_func(wsPhasePattern))) * 2*np.pi #Normalize phase array and multiply by 2 pi
wsPhase[wsAttn==0] = wsPhaseDispersion

# plt.plot(wsFreq, wsAttn)
plt.plot(wsFreq, wsPhase)
plt.xlabel('Frequency (THz)')
plt.ylabel("Phase (rad)")
plt.show()
# waveshaper.upload_profile(wsFreq, wsAttn, wsPhase, wsPort)
