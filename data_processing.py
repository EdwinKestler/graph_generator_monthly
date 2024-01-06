import pandas as pd
from bokeh.plotting import figure, output_file, save
from bokeh.models import Range1d, LinearAxis, HoverTool
import os

def read_and_prepare_data(csv_file_path):
    df = pd.read_csv(csv_file_path, header=0, delimiter=',')
    df['fecha'] = pd.to_datetime(df['fecha'], format="%d/%m/%Y")
    return df

def prepare_data_for_graphs(df):
    grouped_data = df.groupby('Nombre')
    return grouped_data

def process_grouped_data(name, group, directory_img, directory_html):
    estacion = name
    df = group

    # Process the data
    df['fecha'] = pd.to_datetime(df['fecha'], format="%d/%m/%Y")
    latest_date = df['fecha'].max()
    thirty_days_ago = latest_date - pd.Timedelta(days=30)
    last_30_days_data = df[df['fecha'] >= thirty_days_ago]
    last_30_days_data = last_30_days_data.sort_values("fecha")
    last_30_days_data[['Nombre']] = last_30_days_data[['Nombre']].replace('_', ' ', regex=True)

    # Extract necessary data
    lluvia = last_30_days_data['lluvia']
    tmin = last_30_days_data['tmin']
    tseca = last_30_days_data['tseca']
    tmax = last_30_days_data['tmax']
    fecha = last_30_days_data['fecha']

    # Create the Bokeh plot
    fig = figure(x_axis_type='datetime', title=estacion, height=400, width=800, toolbar_location='below',
                 y_axis_label="Precipitación (mm)", y_range=(-5, 90), background_fill_color='white',
                 background_fill_alpha=0.6, tools="save,pan,box_zoom,reset,wheel_zoom")
    fig.yaxis.axis_label_text_font_size = "8pt"
    fig.title.text_font_size = '8pt'
    fig.left[0].formatter.use_scientific = False

    # Add second axis for temperature
    fig.extra_y_ranges = {"temp_range": Range1d(start=-5, end=40)}
    fig.add_layout(LinearAxis(y_range_name="temp_range", axis_label="Temperatura (°C)"), 'right')

    # Add lines and circles
    fig.line(fecha, lluvia, line_color='navy', line_width=1, legend_label='Precipitación', name='lluvia')
    fig.line(fecha, tseca, line_color='seagreen', line_width=1, line_dash='dashed', legend_label='Temperatura media',
             name='tseca', y_range_name='temp_range')
    fig.circle(fecha, tmin, fill_color='deepskyblue', line_color='blue', size=3, legend_label='Temperatura min',
               name='tmin', y_range_name='temp_range')
    fig.circle(fecha, tmax, fill_color='firebrick', line_color='red', size=3, legend_label='Temperatura max',
               name='tmax', y_range_name='temp_range')

    fig.legend.location = 'top_left'
    fig.title.text_font_size = '10pt'
    fig.yaxis.axis_label_text_font_size = "10pt"

    # Add tooltips
    tooltips = [("Valor", "@y"), ("Fecha", "@x{%F}")]
    formatters = {'@x': 'datetime'}
    hover = HoverTool(tooltips=tooltips, formatters=formatters, mode='vline')
    fig.add_tools(hover)

    # Generate HTML file and save the plot
    output_file(os.path.join(directory_html, f'{estacion}.html'))
    fig.legend.background_fill_alpha = 0.5
    fig.legend.label_text_font_size = "8pt"
    fig.legend.spacing = 1
    save(fig)

    # Prepare data for further processing or matplotlib plotting
    data = {
        'fecha': fecha,
        'lluvia': lluvia,
        'tmin': tmin,
        'tseca': tseca,
        'tmax': tmax,
        'estacion': estacion,
        'directory_img': directory_img
    }

    return data