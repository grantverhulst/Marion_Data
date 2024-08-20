# Marion Weather Data Processing

## Project Description
This project contains Python scripts for downloading and processing weather data for Marion Lake. It automates the extraction of data from the USACE Marion Reservoir webpage, processes it, and stores it in CSV files for meteorological data, inflow, and outflow from Marion Lake.

## Features
- Automatically scrapes hourly weather data from the USACE Marion Reservoir webpage.
- Processes and cleans the data.
- Outputs the data into structured CSV files for use with the General Lake Model.

## Installation
Clone this repository to your local machine using:

git clone https://your-repository-url-here

To run these scripts, you will need Python 3 and some additional packages. Install the required packages using pip:

pip install numpy requests beautifulsoup4

## Usage
Navigate to the project directory and run the scripts as follows:

For daily weather data updates:
python marionweather.py

To initialize data collection from a specific past date to yesterday:
python init_marion.py

## Files
- `marionweather.py`: Script for daily updates.
- `init_marion.py`: Script for initializing data collection.

## Licensing
This project is licensed under the MIT License - see the LICENSE file for details.

## Contact
For support, contact grantverhulst@gmail.com.