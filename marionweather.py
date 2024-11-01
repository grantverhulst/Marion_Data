import csv
import re
import numpy as np
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

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
meteo_filename = "meteo_MarionLake.csv"
inflow_filename = 'inflow.csv'
outflow_filename = 'outflow.csv'

# Opening all files
files = {
    'meteo': open(meteo_filename, 'a', newline=''),
    'inflow': open(inflow_filename, 'a', newline=''),
    'outflow': open(outflow_filename, 'a', newline='')
}
writers = {
    key: csv.writer(file) for key, file in files.items()
}

# Checking the last recorded date
with open(meteo_filename, 'r') as file:
    for line in file:
        last_line = line
last_date = datetime.strptime(last_line[0:10], '%Y-%m-%d').date() if last_line else datetime.min.date()
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
        data_lines = re.split(r'(?=\d{2}/\d{2} \d{2}:\d{2})', data_string)[1:]
        for line in data_lines:
            parts = line.split()
            if parts and len(parts) > 10:
                datetime_str = convert_to_datetime(parts[0], parts[1], current_year)
                t = float(parts[7])
                rh = float(parts[10])/100
                inflow_data = [datetime_str, parts[5]] # Inflow
                outflow_data = [datetime_str, parts[6]] # Outflow
                meteo_data = [
                    datetime_str,
                    parts[11],  # ShortWave
                    incoming_longwave_radiation(rh, fahrenheit_to_kelvin(t)), # LongWave
                    t, # Temperature
                    rh, # Relative Humidity
                    parts[9],  # WindSpeed
                    parts[2],  # Rain
                    '0'        # Snow
                ]
                writers['meteo'].writerow(meteo_data)
                writers['inflow'].writerow(inflow_data)
                writers['outflow'].writerow(outflow_data)
        print('Data appended successfully')

# Close all files
for file in files.values():
    file.close()