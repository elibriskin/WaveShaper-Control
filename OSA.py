"""
Author: Camilo Hurtado Ballesteros
email: churtadob@unal.edu.co
Date: 15/04/2024
Description: This code was developed with the purpose of establishing a connection between an OSA (Yokogawa AQ6370D)
and a computer via an Ethernet protocol for data acquisition. The acquired results are saved in a specific file and
directory, ensuring efficient and accurate data storage.


Version: 2.0


Inputs:
    - device_address (str): The IP address of the OSA device (e.g., "168.176.118.23").
    - device_port (int): The port number for Ethernet communication (e.g., 10001).
    - target_data_length (None or int): The length of data to be acquired, initially set to None.
    - iteration_count (int): The current iteration counter, initialized at 0.
    - required_iterations (int): The total number of iterations to be performed, set to 50.
    - folder_path (str): The directory where the acquired data will be saved
    (e.g., "D:\\Supercontinium\\FioCoherenceMeasurements\\DifferentPosition_EqualCurrent").
Outputs:
    - CSV file: The acquired data, including wavelengths and intensities, is saved to a CSV file in the specified
      directory. The file is generated using the following function:
      `AQ6370D.save_data_to_csv(longitudes_de_onda, intensities, folder_path, iteration_count)`

Notes:
    This is an initial version of the code. For further information or inquiries, please refer to the contact email
    provided above. The script is fully functional, but ensure that the configuration of your OSA matches the parameters
    specified in the script.

Usage:

    Ensure that both the OSA and the PC are connected to a network socket or router, allowing each device to be
    assigned a valid IP address for establishing the connection. Before running the script, you may perform a PING
    integration.py to the OSA from the Linux terminal or Windows PowerShell to verify if the device is responding and properly
    connected.
"""

import socket
import csv
import numpy as np
import time
import matplotlib.pyplot as plt
import os

class OSA:
    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.socket = None
        self.data = []  # Array to store data
        self.sweep_modes = {
            "SINGLE": 1,
            "REPEAT": 2,
            "AUTO": 3
        }

    def open_socket(self):
        '''
        Opens ethernet socket connection
        '''
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(20)

            #Connect to socket
            self.socket.connect((self.address, self.port))
            print("Connection established with device at", self.address)
        except Exception as e:
            print("Error:", e)

    def close_socket(self):
        '''
        Closes ethernet socket connection
        '''
        if self.socket:
            self.socket.close()
            print("Connection closed.")

    def send_command(self, command):
        '''
        This function sends remote commands to the OSA.
        '''
        try:
            if self.socket:
                #Send remote command to OSA
                self.socket.send((command + "\r\n").encode())
                time.sleep(0.2)
            else:
                print("Socket not initialized.")
        except Exception as e:
            print("Error:", e)

    def __query__(self, command):
        '''
        This method is used to query data from the OSA
        '''
        self.send_command(command)
        try:
            if self.socket:
                received_data = b''
                while True:
                    try:
                        chunk = self.socket.recv(4096)
                        if not chunk:
                            break
                        received_data += chunk
                        time.sleep(0.2)  # Small delay to ensure complete reception
                    except socket.timeout:
                        print("Socket timed out, stopping reception.")
                        break
                print(f"Received data length: {len(received_data)}")
                return received_data.decode('utf-8', errors='ignore')
            else:
                print("Socket not initialized.")
                return None
        except Exception as e:
            print("Error receiving trace data:", e)
            return None

    def initialize_connection(self):
        '''
        This method initializes connection to the OSA.
        '''
        try:
            self.open_socket()
            self.send_command("open \"anonymous\"")
        except Exception as e:
            print("Error initializing connection:", e)

    def set_start_wavelength(self, wavelength_start):
        '''
        This method sets the starting wavelength of the OSA.
        '''
        self.send_command(f":sens:wav:start {wavelength_start}nm")

    def set_stop_wavelength(self, wavelength_stop):
        '''
        This method sets the stop wavelength of the OSA.
        '''
        self.send_command(f":sens:wav:stop {wavelength_stop}nm")

    def set_wavelength_range(self, wavelength_start, wavelength_stop):
        '''
        This method sets the wavelength range of the OSA.
        '''
        self.send_command(f":sens:wav:start {wavelength_start}nm")

        self.send_command(f":sens:wav:stop {wavelength_stop}nm")

    def set_wavelength_span(self, span):
        '''
        This method sets the span of the wavelength range.
        '''
        self.send_command(f":sens:wav:span {span}nm")

    def set_sweep_mode(self, sweep_mode):
        '''
        This method sets the mode for wavelength sweep. Choices
        are 'AUTO', 'REPEAT', and 'SINGLE.'
        '''
        if sweep_mode in self.sweep_modes.keys():
            self.command(f":init:smode {self.sweep_modes[sweep_mode]}")
        else:
            raise Exception(f"Invalid sweep mode! Sweep modes are {self.sweep_modes.keys()}")
    def set_resolution(self, resolution):
        '''
        This method sets the resolution of the OSA in nanometers.
        '''
        self.send_command(f":sens:band:resolution {resolution}nm")

    def get_single_trace(self, wavelength_start, wavelength_stop):
        '''
        This method is used to get a trace of an optical spectrum.
        '''
        try:
            self.initialize_connection()

            #Resets device
            self.send_command("*RST")

            #Sets GPIB command format
            self.send_command("CFORM1")

            #Set wavelength range
            self.send_command(f":sens:wav:start {wavelength_start}nm")
            self.send_command(f":sens:wav:stop {wavelength_stop}nm")

            #Sets measurement sensitivity to high
            self.send_command(":sens:sens HIGH2")

            #Set wavelength sweep speed
            self.send_command(":sens:sens:speed 2x")

            #Sets automatic sampling of points
            self.send_command(":sens:sweep:points:auto on")
            print("Preconfig done")

            #Initiates sweep mode to SINGLE sweep
            self.send_command(":init:smode 1")
            print("SMODE set")

            #Clears status register
            self.send_command("*CLS")
            print("CLS command sent")

            #Initiates wavelength sweep
            self.send_command(":init")
            print("INIT command sent")

            #Gets trace
            trace_data = self.__query__(':TRACE:Y? TRA')
            print("Query done")
            print(trace_data[:40])

            if trace_data:
                if 'ready' in trace_data:

                    #Parses trace data format
                    text_after_ready = trace_data.split('ready', 1)[1]

                    #Creates array of intensities
                    intensities = np.array([float(intensity) for intensity in text_after_ready.split(",") if intensity.strip()])


                    # Use the wavelength from the current measurement
                    wavelengths = np.linspace(wavelength_start, wavelength_stop, len(intensities))

            return wavelengths, intensities
        except Exception as e:
            print("Error getting single trace:", e)
        finally:
            self.close_socket()

    def analyze_spectrum(self):
        pass

    def ArrayForLabview(self, InputArray, wavelengthStart, wavelengthEnd):
        NumArray = InputArray.split('ready', 1)[1]
        OutputArray = np.array([float(numero) for numero in NumArray.split(",")])
        ArrayWavelength = np.linspace(wavelengthStart, wavelengthEnd, len(InputArray))
        return ArrayWavelength, OutputArray

    @staticmethod
    def save_data_to_csv(wavelengths, intensities, folder_path, iteration_count):
        filename = f"trace_data_{iteration_count}_Current_7_22_Pos_11_0_cm_100Hz.csv"
        file_path = os.path.join(folder_path, filename)
        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Wavelength (nm)", "Intensity"])
            writer.writerows(zip(wavelengths, intensities))
        print(f"Data for iteration {iteration_count} saved to {file_path}")

    @staticmethod
    def plot_data(wavelengths, intensities, iteration_count):
        plt.figure(figsize=(10, 6))
        plt.plot(wavelengths, intensities, label=f'Intensity {iteration_count}', color='b')
        plt.title(f'Intensity Spectrum Iteration {iteration_count}')
        plt.xlabel('Wavelength (nm)')
        plt.ylabel('Intensity')
        plt.grid(True)
        plt.legend()
        plt.show()


