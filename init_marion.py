import csv
import re
import numpy as np
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

#functions for unit conversions and longwave estimation
def inches_to_meters(inches):
    return inches * 0.0254
def mph_to_mps(mph):
    return mph * 0.44704
def cfs_to_cms(cfs):
    return cfs * 0.0283168
def fahrenheit_to_celsius(F):
    return (F - 32) * 5 / 9
def fahrenheit_to_kelvin(F):
    return (F - 32) * 5 / 9 + 273.15
def saturation_vapor_pressure(T):
    T_C = T - 273.15
    return 6.112 * np.exp((17.67 * T_C) / (T_C + 243.5))
def incoming_longwave_radiation(RH, T):
    P_w = RH * saturation_vapor_pressure(T)
    epsilon = 1.24 * (P_w / T) ** (1/7)
    sigma = 5.67e-8
    return epsilon * sigma * T ** 4
def convert_to_datetime(date_str, time_str, current_year):
    try:
        date_obj = datetime.strptime(date_str, '%m/%d').replace(year=current_year)
        datetime_obj = datetime.combine(date_obj, datetime.strptime(time_str, '%H:%M').time())
        return datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        return None

base_url = "https://www.swt-wc.usace.army.mil/webdata/gagedata/MLBK1."
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

# Define the filenames
filenames = {
    'meteo': "meteo_MarionLake.csv",
    'inflow': 'inflow.csv',
    'outflow': 'outflow.csv'
}

# Open files in append mode and create writers
files = {name: open(filename, 'a', newline='') for name, filename in filenames.items()}
writers = {name: csv.writer(file) for name, file in files.items()}

# Initialize with correct headers for General Lake Model
for name, writer in writers.items():
    if name == 'meteo':
        writer.writerow(['Date', 'ShortWave', 'LongWave', 'AirTemp', 'RelHum', 'WindSpeed', 'Rain', 'Snow'])
    if name == 'inflow':
        writer.writerow(['Date','FLOW'])
    if name == 'outflow':
        writer.writerow(['Date', name])

# Define the date range
start_date = datetime(2024, 3, 20).date()
end_date = datetime.now().date() - timedelta(days=1)
date_generated = [start_date + timedelta(days=x) for x in range(0, (end_date - start_date).days + 1)]

# Loop over each date in the date range
for single_date in date_generated:
    formatted_date = single_date.strftime('%Y%m%d')
    full_url = f"{base_url}{formatted_date}.html"
    page = requests.get(full_url, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')
    results = soup.find('pre', class_='table-data')
    current_year = single_date.year

    if results:
        data_string = results.text.strip().replace('----', '0') # replaces nan with 0
        data_lines = re.split(r'(?=\d{2}/\d{2} \d{2}:\d{2})', data_string)[1:]
        for line in data_lines:
            parts = line.split()
            if parts and len(parts) > 10:

                datetime_str = convert_to_datetime(parts[0], parts[1], current_year)
                t = float(parts[7]) # temperature in F
                rh = float(parts[10]) # relative humidity
                ws = float(parts[9]) # wind speed in mph
                rain = float(parts [2]) # rain in inches
                inflow = float(parts[5])  # Inflow in cfs
                outflow = float(parts[6])  # Outflow in cfs

                meteo_data = [
                    datetime_str,
                    parts[11],  # ShortWave
                    incoming_longwave_radiation(rh/100, fahrenheit_to_kelvin(t)), # LongWave
                    fahrenheit_to_celsius(t), # Temperature in C
                    rh, # Relative Humidity
                    mph_to_mps(ws),  # WindSpeed in m/s
                    inches_to_meters(rain),  # Rain in meters
                    '0'        # Snow
                ]
                inflow_data = [datetime_str, cfs_to_cms(inflow)]  # inflow in cms
                outflow_data = [datetime_str, cfs_to_cms(outflow)] # outflow in cms

                writers['meteo'].writerow(meteo_data)
                writers['inflow'].writerow(inflow_data)
                writers['outflow'].writerow(outflow_data)

# Close all files
for file in files.values():
    file.close()

# Create files with nan values

# Define the filenames
filenames = {
    'met_nan': "met_nan.csv",
    'inflow_nan': 'inflow_nan.csv',
    'outflow_nan': 'outflow_nan.csv'
}

# Open files in append mode and create writers
files = {name: open(filename, 'a', newline='') for name, filename in filenames.items()}
writers = {name: csv.writer(file) for name, file in files.items()}

# Initialize with correct headers for General Lake Model
for name, writer in writers.items():
    if name == 'met_nan':
        writer.writerow(['Date', 'ShortWave', 'LongWave', 'AirTemp', 'RelHum', 'WindSpeed', 'Rain', 'Snow'])
    if name == 'inflow_nan':
        writer.writerow(['Date','FLOW'])
    if name == 'outflow_nan':
        writer.writerow(['Date', name])

# Loop over each date in the date range
for single_date in date_generated:
    formatted_date = single_date.strftime('%Y%m%d')
    full_url = f"{base_url}{formatted_date}.html"
    page = requests.get(full_url, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')
    results = soup.find('pre', class_='table-data')
    current_year = single_date.year

    if results:
        data_string = results.text.strip().replace('----', 'NaN') # replaces nan with 0
        data_lines = re.split(r'(?=\d{2}/\d{2} \d{2}:\d{2})', data_string)[1:]
        for line in data_lines:
            parts = line.split()
            if parts and len(parts) > 10:

                datetime_str = convert_to_datetime(parts[0], parts[1], current_year)
                t = float(parts[7]) # temperature in F
                rh = float(parts[10]) # relative humidity
                ws = float(parts[9]) # wind speed in mph
                rain = float(parts [2]) # rain in inches
                inflow = float(parts[5])  # Inflow in cfs
                outflow = float(parts[6])  # Outflow in cfs

                meteo_data = [
                    datetime_str,
                    parts[11],  # ShortWave
                    incoming_longwave_radiation(rh/100, fahrenheit_to_kelvin(t)), # LongWave
                    fahrenheit_to_celsius(t), # Temperature in C
                    rh, # Relative Humidity
                    mph_to_mps(ws),  # WindSpeed in m/s
                    inches_to_meters(rain),  # Rain in meters
                    '0'        # Snow
                ]
                inflow_data = [datetime_str, cfs_to_cms(inflow)]  # inflow in cms
                outflow_data = [datetime_str, cfs_to_cms(outflow)] # outflow in cms

                writers['met_nan'].writerow(meteo_data)
                writers['inflow_nan'].writerow(inflow_data)
                writers['outflow_nan'].writerow(outflow_data)

# Close all files
for file in files.values():
    file.close()