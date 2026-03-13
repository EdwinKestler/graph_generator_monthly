import pandas as pd
import sys

df = pd.read_csv('datos-csv/download-database.csv', low_memory=False)
out = []
out.append(f"Columns: {list(df.columns)}")
out.append(f"Total rows: {len(df)}")
stations = df['Nombre'].unique()
out.append(f"Station count: {len(stations)}")
for s in sorted(stations):
    row = df[df['Nombre'] == s].iloc[0]
    lat = row.get('Latitud', 'N/A')
    lon = row.get('Longitud', 'N/A')
    alt = row.get('Altitud', 'N/A')
    out.append(f"  {s} | lat={lat} lon={lon} alt={alt}")

with open('_stations_out.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print("Done")
