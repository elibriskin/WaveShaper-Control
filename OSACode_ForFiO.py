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

class AQ6370D:
    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.socket = None
        self.data = []  # Array to store data

    def open_socket(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(20)
            self.socket.connect((self.address, self.port))
            print("Connection established with device at", self.address)
        except Exception as e:
            print("Error:", e)

    def close_socket(self):
        if self.socket:
            self.socket.close()
            print("Connection closed.")

    def send_command(self, command):
        try:
            if self.socket:
                self.socket.send((command + "\r\n").encode())
                time.sleep(0.2)
            else:
                print("Socket not initialized.")
        except Exception as e:
            print("Error:", e)

    def __query__(self, command):
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
        try:
            self.open_socket()
            self.send_command("open \"anonymous\"")
        except Exception as e:
            print("Error initializing connection:", e)

    def get_single_trace(self, wavelength_start, wavelength_stop):
        try:
            self.initialize_connection()
            self.send_command("*RST")
            self.send_command("CFORM1")
            self.send_command(f":sens:wav:start {wavelength_start}nm")
            self.send_command(f":sens:wav:stop {wavelength_stop}nm")
            self.send_command(":sens:sens HIGH2")
            self.send_command(":sens:sens:speed 2x")
            self.send_command(":sens:sweep:points:auto on")
            print("Preconfig done")
            self.send_command(":init:smode 1")
            print("SMODE set")
            self.send_command("*CLS")
            print("CLS command sent")
            self.send_command(":init")
            print("INIT command sent")
            trace_data = self.__query__(':TRACE:Y? TRA')
            print("Query done")
            print(trace_data[:40])
            return trace_data
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

if __name__ == "__main__":
    start_time = time.time()

    device_address = "168.176.118.23"
    device_port = 10001

    target_data_length = None
    iteration_count = 0
    required_iterations = 50

    folder_path = "D:\\Supercontinium\\FioCoherenceMeasurements\\DifferentPosition_EqualCurrent"

    while iteration_count < required_iterations:
        osa = AQ6370D(device_address, device_port)
        trace_data = osa.get_single_trace()

        if trace_data:
            if 'ready' in trace_data:
                text_after_ready = trace_data.split('ready', 1)[1]
                intensities = np.array([float(numero) for numero in text_after_ready.split(",") if numero.strip()])

                # Check data length and ensure consistency
                if target_data_length is None:
                    target_data_length = len(intensities)
                    iteration_count += 1
                    print('Number Iteration :', iteration_count)
                elif len(intensities) == target_data_length:
                    iteration_count += 1
                    print('Number Iteration :', iteration_count)
                else:
                    print(f"Data length mismatch: expected {target_data_length}, got {len(intensities)}. Discarding this data.")
                    continue

                # Use the wavelength from the current measurement
                longitud_onda_inicial = 600
                longitud_onda_final = 1100
                longitudes_de_onda = np.linspace(longitud_onda_inicial, longitud_onda_final, len(intensities))

                # Save data to CSV
                AQ6370D.save_data_to_csv(longitudes_de_onda, intensities, folder_path, iteration_count)

                # Optionally, plot the data
                # AQ6370D.plot_data(longitudes_de_onda, intensities, iteration_count)
            else:
                print("No valid data received. Skipping iteration.")

        # Adding a short delay between iterations to avoid overwhelming the remote host
        time.sleep(0.1)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Script execution time: {elapsed_time:.2f} seconds")

    print("Work done")
