from bokeh.models import Range1d, LinearAxis
from bokeh.models.tools import HoverTool
from bokeh.plotting import figure, output_file
import pandas as pd
import json
from bokeh.io import export_png, save
from selenium import webdriver

#Driver of GoogleChrome to save png images
driver = webdriver.Chrome(executable_path='settings_driver/chromedriver')

# Directorios de entrada y salida
directory = "html_output/"
directory2 = "img_output/"

# Leer el archivo CSV de entrada
df = pd.read_csv('database.csv', header=0, delimiter=',')

# Convertir la columna FECHA a formato datetime y ordenar el dataframe
df['fecha'] = pd.to_datetime(df['fecha'], format="%d/%m/%Y")

# Obtener la fecha más reciente en el dataframe
latest_date = df['fecha'].max()

# Calcular la fecha de hace 30 días a partir de la fecha más reciente
thirty_days_ago = latest_date - pd.Timedelta(days=30)

# Filtrar los datos para que solo incluyan los de los últimos 30 días
last_30_days_data = df[df['fecha'] >= thirty_days_ago]
last_30_days_data = last_30_days_data.sort_values("fecha")

# Obtener la lista de estaciones disponibles en el dataframe
estaciones = last_30_days_data["Nombre"].unique()

# Crear un gráfico y un archivo HTML para cada estación
for estacion in estaciones:
    # Filtrar los datos para la estación actual
    data = df[df['estacion'] == estacion]
    # filtrar los datos por la estación (k)
    gk = last_30_days_data.groupby(['Nombre'])
    lluvia = gk.get_group(estacion)['lluvia']
    tmin=gk.get_group(estacion)['tmin']
    tseca=gk.get_group(estacion)['tseca']
    tmax=gk.get_group(estacion)['tmax']
    fecha=gk.get_group(estacion)['fecha']

    fig = figure(x_axis_type='datetime', title=estacion, plot_height=400, plot_width=800, toolbar_location='below',
                    y_axis_label="Precipitación (mm)", y_range=(-5, 90), background_fill_color='white', 
                    background_fill_alpha=0.6, tools="save,pan,box_zoom,reset,wheel_zoom")


    fig.yaxis.axis_label_text_font_size = "8pt"
    fig.title.text_font_size = '8pt'
    fig.left[0].formatter.use_scientific = False

    # agregar el segundo eje para la temperatura
    fig.extra_y_ranges = {"temp_range": Range1d(start=-5, end=40)}
    fig.add_layout(LinearAxis(y_range_name="temp_range", axis_label="Temperatura (°C)"), 'right')


    # agregar las líneas y los círculos
    fig.line(fecha, lluvia, line_color='navy', line_width=1, legend_label='Precipitación',
                name='precip')

    fig.line(fecha, tseca, line_color='seagreen', line_width=1, line_dash='dashed', legend_label='Temperatura media', 
                name='tseca',y_range_name='temp_range')
    fig.circle(fecha, tmin, fill_color='deepskyblue', line_color='blue', size=3,
                legend_label='Temperatura min', name='tmin',y_range_name='temp_range')
    fig.circle(fecha, tmax, fill_color='firebrick', line_color='red', size=3,
                legend_label='Temperatura max', name='tmax',y_range_name='temp_range')

    fig.legend.location = 'top_left'
    fig.title.text_font_size = '10pt'
    fig.yaxis.axis_label_text_font_size = "10pt"

    # agregar etiquetas a las líneas y los círculos
    tooltips = [
        ("Valor", "@y"),
        ("Fecha", "@x{%F}")
    ]
    formatters = {
        '@x': 'datetime'
    }
    #Hola
    hover = HoverTool(names=['lluvia', 'tseca', 'tmin', 'tmax'], tooltips=tooltips, formatters=formatters
                        )
    fig.add_tools(hover)

    # generar el archivo html y mostrar la gráfica
    output_file(f'{directory}{estacion}.html')             
    fig.legend.background_fill_alpha = 0.5
    fig.legend.label_text_font_size = "8pt"
    fig.legend.spacing = 1
    save(fig)
    export_png(fig, filename=f"{directory2}{estacion}.png")



