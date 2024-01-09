import pandas as pd
from bokeh.plotting import figure, output_file, save
from bokeh.models import Range1d, LinearAxis, HoverTool
import os

# Constants
DATE_FORMAT = "%d/%m/%Y"

def read_and_prepare_data(csv_file_path):
    """
    Read and prepare data from a CSV file.

    Args:
        csv_file_path (str): Path to the CSV file.

    Returns:
        pd.DataFrame: Prepared DataFrame.
    """
    df = pd.read_csv(csv_file_path, header=0, delimiter=',')
    df['fecha'] = pd.to_datetime(df['fecha'], format=DATE_FORMAT)
    return df

def prepare_data_for_graphs(df):
    """
    Group data for graph preparation.

    Args:
        df (pd.DataFrame): Input DataFrame.

    Returns:
        pd.DataFrameGroupBy: Grouped data.
    """
    return df.groupby('Nombre')

def process_grouped_data(name, group, directory_img, directory_html):
    """
    Process and plot data for each group.

    Args:
        name (str): Station name.
        group (pd.DataFrame): Grouped data.
        directory_img (str): Directory for images.
        directory_html (str): Directory for HTML output.

    Returns:
        dict: Data for further processing or matplotlib plotting.
    """
    df = group.copy()
    df['fecha'] = pd.to_datetime(df['fecha'], format=DATE_FORMAT)
    latest_date = df['fecha'].max()
    month_year_str = latest_date.strftime("%m-%Y")
    thirty_days_ago = latest_date - pd.Timedelta(days=30)
    last_30_days_data = df[df['fecha'] >= thirty_days_ago].sort_values("fecha")
    last_30_days_data['Nombre'] = last_30_days_data['Nombre'].replace('_', ' ', regex=True)

    # Plotting
    fig = create_bokeh_plot(last_30_days_data, name)
    save_plot(fig, name, month_year_str, directory_html)

    # Data for further processing or matplotlib plotting
    return extract_plotting_data(last_30_days_data, name, directory_img)

def create_bokeh_plot(data, station_name):
    """
    Create Bokeh plot for the given data.

    Args:
        data (pd.DataFrame): Data for plotting.
        station_name (str): Station name.

    Returns:
        bokeh.plotting.Figure: Bokeh plot.
    """
    fig = figure(
        x_axis_type='datetime', title=station_name, height=400, width=800,
        toolbar_location='below', y_axis_label="Precipitación (mm)",
        y_range=(-5, 90), background_fill_color='white', background_fill_alpha=0.6,
        tools="save,pan,box_zoom,reset,wheel_zoom"
    )
    configure_plot(fig)
    add_plot_elements(fig, data)
    return fig

def configure_plot(fig):
    """Configure plot appearance and settings."""
    fig.yaxis.axis_label_text_font_size = "8pt"
    fig.title.text_font_size = '8pt'
    fig.left[0].formatter.use_scientific = False
    fig.extra_y_ranges = {"temp_range": Range1d(start=-5, end=40)}
    fig.add_layout(LinearAxis(y_range_name="temp_range", axis_label="Temperatura (°C)"), 'right')

def add_plot_elements(fig, data):
    """Add lines, circles, and tooltips to the plot."""
    fig.line(data['fecha'], data['lluvia'], line_color='navy', line_width=1, legend_label='Precipitación', name='lluvia')
    fig.line(data['fecha'], data['tseca'], line_color='seagreen', line_width=1, line_dash='dashed', legend_label='Temperatura media', name='tseca', y_range_name='temp_range')
    fig.circle(data['fecha'], data['tmin'], fill_color='deepskyblue', line_color='blue', size=3, legend_label='Temperatura min', name='tmin', y_range_name='temp_range')
    fig.circle(data['fecha'], data['tmax'], fill_color='firebrick', line_color='red', size=3, legend_label='Temperatura max', name='tmax', y_range_name='temp_range')

    fig.legend.location = 'top_left'
    fig.title.text_font_size = '10pt'
    fig.yaxis.axis_label_text_font_size = "10pt"
    add_tooltips(fig)

def add_tooltips(fig):
    """Add tooltips to the plot."""
    tooltips = [("Valor", "@y"), ("Fecha", "@x{%F}")]
    formatters = {'@x': 'datetime'}
    fig.add_tools(HoverTool(tooltips=tooltips, formatters=formatters, mode='vline'))

def save_plot(fig, station_name, month_year_str, directory_html):
    """
    Save the plot as an HTML file.

    Args:
        fig (bokeh.plotting.Figure): Bokeh plot.
        station_name (str): Station name.
        month_year_str (str): Month and year as a string.
        directory_html (str): Directory for HTML output.
    """
    filename = f'{station_name}_{month_year_str}.html'
    output_file(os.path.join(directory_html, filename))
    fig.legend.background_fill_alpha = 0.5
    fig.legend.label_text_font_size = "8pt"
    fig.legend.spacing = 1
    save(fig)

def extract_plotting_data(data, station_name, directory_img):
    """
    Extract and return data for plotting.

    Args:
        data (pd.DataFrame): Data for plotting.
        station_name (str): Station name.
        directory_img (str): Directory for images.

    Returns:
        dict: Data for plotting.
    """
    return {
        'fecha': data['fecha'],
        'lluvia': data['lluvia'],
        'tmin': data['tmin'],
        'tseca': data['tseca'],
        'tmax': data['tmax'],
        'estacion': station_name,
        'directory_img': directory_img
    }
    
    