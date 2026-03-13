"""Test the timestamped download filename logic."""
import os, sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pandas as pd
from download_database import download_file_from_google_drive

data_dir = os.path.join(ROOT, 'data')
temp_path = os.path.join(data_dir, '_download_temp.csv')

print('Downloading...')
success = download_file_from_google_drive('19gcM1e5rb-HvJ-MVhNSZgsinNhN0S79Y', temp_path)
print(f'Download success: {success}')
assert success, 'Download failed'

df_dates = pd.read_csv(temp_path, usecols=['fecha'], low_memory=False)
sample = str(df_dates['fecha'].dropna().iloc[0]).strip()
date_fmt = '%Y-%m-%d' if len(sample) >= 10 and sample[4] == '-' else '%d/%m/%Y'
fechas = pd.to_datetime(df_dates['fecha'], format=date_fmt)
data_start = fechas.min().strftime('%Y%m')
data_end   = fechas.max().strftime('%Y%m')

download_date = date.today().strftime('%Y%m%d')
final_name = f'insivumeh_{download_date}_{data_start}_a_{data_end}.csv'
final_path = os.path.join(data_dir, final_name)

os.replace(temp_path, final_path)

print(f'Saved as:    {final_name}')
print(f'Data period: {data_start[:4]}-{data_start[4:]} to {data_end[:4]}-{data_end[4:]}')
print(f'File size:   {os.path.getsize(final_path):,} bytes')
print(f'Temp removed: {not os.path.exists(temp_path)}')
