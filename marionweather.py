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

# File paths for standard and NaN files
file_paths = {
    'meteo': "meteo_MarionLake.csv",
    'inflow': 'inflow.csv',
    'outflow': 'outflow.csv',
    'met_nan': "met_nan.csv",
    'inflow_nan': 'inflow_nan.csv',
    'outflow_nan': 'outflow_nan.csv',
}

# Open all files in append mode
files = {key: open(path, 'a', newline='') for key, path in file_paths.items()}
writers = {key: csv.writer(file) for key, file in files.items()}

# Check the last recorded date from the meteo file
with open(file_paths['meteo'], 'r') as file:
    last_line = file.readlines()[-1] if file.readable() else None
if last_line:
    last_datetime_str = last_line.split(',')[0]
    last_date = datetime.strptime(last_datetime_str, '%Y-%m-%d %H:%M:%S').date()
else:
    last_date = datetime.min.date()

yesterday = datetime.now().date() - timedelta(days=1)

if last_date == yesterday:
    print("Data is up to date. No action required.")
else:
    formatted_date = yesterday.strftime('%Y%m%d')
    full_url = f"{base_url}{formatted_date}.html"
    page = requests.get(full_url, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')
    results = soup.find('pre', class_='table-data')
    current_year = datetime.now().year

    if results:
        data_string = results.text.strip().replace('----', '0')
        data_nan_string = results.text.strip().replace('----', 'NaN')
        data_lines = re.split(r'(?=\d{2}/\d{2} \d{2}:\d{2})', data_string)[1:]
        data_nan_lines = re.split(r'(?=\d{2}/\d{2} \d{2}:\d{2})', data_nan_string)[1:]

        for standard_line, nan_line in zip(data_lines, data_nan_lines):
            parts = standard_line.split()
            parts_nan = nan_line.split()

            if parts and len(parts) > 10:
                datetime_str = convert_to_datetime(parts[0], parts[1], current_year)
                t = float(parts[7])
                rh = float(parts[10]) / 100

                # Standard data
                inflow_data = [datetime_str, cfs_to_cms(float(parts[5]))]
                outflow_data = [datetime_str, cfs_to_cms(float(parts[6]))]
                meteo_data = [
                    datetime_str,
                    float(parts[11]),
                    incoming_longwave_radiation(rh, fahrenheit_to_kelvin(t)),
                    fahrenheit_to_celsius(t),
                    rh * 100,
                    mph_to_mps(float(parts[9])),
                    inches_to_meters(float(parts[2])),
                    '0'
                ]

                # NaN data
                inflow_nan_data = [datetime_str, parts_nan[5]]
                outflow_nan_data = [datetime_str, parts_nan[6]]
                meteo_nan_data = [
                    datetime_str,
                    parts_nan[11],
                    incoming_longwave_radiation(rh, fahrenheit_to_kelvin(t)) if parts_nan[11] != 'NaN' else 'NaN',
                    fahrenheit_to_celsius(t) if parts_nan[7] != 'NaN' else 'NaN',
                    parts_nan[10],
                    parts_nan[9],
                    parts_nan[2],
                    '0'
                ]

                # Append data to the respective files
                writers['meteo'].writerow(meteo_data)
                writers['inflow'].writerow(inflow_data)
                writers['outflow'].writerow(outflow_data)

                writers['met_nan'].writerow(meteo_nan_data)
                writers['inflow_nan'].writerow(inflow_nan_data)
                writers['outflow_nan'].writerow(outflow_nan_data)

        print("Data appended successfully.")

# Close all files
for file in files.values():
    file.close()