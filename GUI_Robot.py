# Python File for streamlit tools
# Sales Baños y Cocna
# 03-August-2021
# ----------------------------------------------------------------------------------------------------------------------
# Libraries
import datetime
import calendar as cl

import numpy as np
import pandas as pd

import streamlit.components.v1 as components
from pivottablejs import pivot_ui

from st_aggrid import AgGrid, DataReturnMode, GridUpdateMode, GridOptionsBuilder

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import pyodbc

import streamlit as st

# ----------------------------------------------------------------------------------------------------------------------
# Streamlit Setting
st.set_page_config(page_title="IIOT - Corona",
                   initial_sidebar_state="collapsed",
                   page_icon="📈",
                   layout="wide")

tabs = ["Celula de Esmaltado", "Pre-Secadero"]
page = st.sidebar.radio("Tabs", tabs)

@st.cache(persist=False, allow_output_mutation=True, suppress_st_warning=True, show_spinner=False)

# ----------------------------------------------------------------------------------------------------------------------
# Function definition
def load_data(folder="./Data/Raw/", filename="tabla_robot1_2021_04_22_1012.csv"):
    """
    Función que carga el archivo csv guardado al conectar con la base de datos y devuelve un dataframe
    """
    df = pd.read_csv(folder + filename, )

    return df

def fecha_format(df):
    """
    Función que hace el manejo de la columna de fecha de la base de datos
    """
    # Organizar el tema de fecha
    df["fecha"] = pd.to_datetime(df['fecha'], format='%Y/%m/%d', exact=False)
    df['fecha'] += pd.to_timedelta(df["hora"], unit='h')
    df['fecha'] += pd.to_timedelta(df["minuto"], unit='m')
    df['fecha'] += pd.to_timedelta(df["segundo"], unit='s')

    # Separar los años, meses y días
    df["año"] = df["fecha"].dt.year
    df["mes"] = df["fecha"].dt.month
    df["dia"] = df["fecha"].dt.day
    df["ndia"] = df["fecha"].dt.day_name()

    # Creo columna de fecha organizacional
    df["fecha_planta"] = [elem - datetime.timedelta(days=1) if df["hora"].iloc[x] < 6 else elem for x, elem in
                          enumerate(df["fecha"])]

    # Organizo las columnas
    re_columns = ['estado', 'fecha', 'referencia', 'peso_antes', 'peso_despues', 'sp_fmasico', 'fmasico',
                  'sp_patomizacion', 'patomizacion',
                  'sp_pabanico', 'pabanico', 'presion_red', 'año', 'mes', 'dia', 'ndia', 'hora', 'minuto', 'segundo',
                  "fecha_planta"]
    df = df[re_columns]

    # Ordeno la data por la fecha
    df = df.sort_values(by='fecha', ascending=True)

    df.set_index("fecha", inplace=True)

    return df

def prev_day(day):
    """
    Función que devuelve el día anterior al entregado, teniendo en cuenta inicio de mes e inicio de año
    INPUT
        day = "2021-02-01"  EN STRING
    OUTPUT
        ini_date = día anterior al día ingresado EN STR
        fin_date = day EN STR
    """
    l_day_n = [int(x) for x in day.split("-")]

    if l_day_n[2] - 1 == 0:
        c_year = l_day_n[0]
        c_month = l_day_n[1] - 1

        if l_day_n[1] - 1 == 0:
            c_year = l_day_n[0] - 1
            c_month = 12
        c_day = cl.monthrange(c_year, c_month)[1]
        # Tomo el dato del día especificado + las horas del turno 3 del día anterior
        ini_date = datetime.date(c_year, c_month, c_day)
        fin_date = datetime.date(l_day_n[0], l_day_n[1], l_day_n[2])
    else:
        # Tomo el dato del día especificado + las horas del turno 3 del día anterior
        ini_date = datetime.date(l_day_n[0], l_day_n[1], l_day_n[2] - 1)
        fin_date = datetime.date(l_day_n[0], l_day_n[1], l_day_n[2])

    return str(ini_date), str(fin_date)

def turno_time(day, turno):
    """
    Función que devuelve el marco de tiempo del turno indicado para filtrar el data set y el titulo de la grafica
    INPUT
        day = "2021-02-01"  EN STRING
        turno = 1 or 2 or 3 EN INT
    OUTPUT
        ini_date = Fecha y hora de inicio del turno EN DATETIME
        fin_date = Fecha y hora de fin del turno EN DATETIME
        title_plot = Titulo para la grafica
    """

    l_day_n = [int(x) for x in day.split("-")]

    # Que pasa si el dia era el 1 del mes o si el mes es el 1 del año....
    if l_day_n[2] - 1 == 0:
        c_year = l_day_n[0]
        c_month = l_day_n[1] - 1

        if l_day_n[1] - 1 == 0:
            c_year = l_day_n[0] - 1
            c_month = 12
        c_day = cl.monthrange(c_year, c_month)[1]

        # Tomo el dato del día especificado + las horas del turno 3 del día anterior
        ini_date = datetime.datetime(c_year, c_month, c_day, 22, 0, 0)
        fin_date = datetime.datetime(l_day_n[0], l_day_n[1], l_day_n[2], 23, 59, 59)
    else:
        # Tomo el dato del día especificado + las horas del turno 3 del día anterior
        ini_date = datetime.datetime(l_day_n[0], l_day_n[1], l_day_n[2] - 1, 22, 0, 0)
        fin_date = datetime.datetime(l_day_n[0], l_day_n[1], l_day_n[2], 23, 59, 59)

    if turno == 1:  # De 6:00 am a 2:00 pm
        ini_date = datetime.datetime(l_day_n[0], l_day_n[1], l_day_n[2], 6, 0, 0)
        fin_date = datetime.datetime(l_day_n[0], l_day_n[1], l_day_n[2], 13, 59, 59)
    elif turno == 2:  # De 2:00 pm a 10:00 pm
        ini_date = datetime.datetime(l_day_n[0], l_day_n[1], l_day_n[2], 14, 0, 0)
        fin_date = datetime.datetime(l_day_n[0], l_day_n[1], l_day_n[2], 21, 59, 59)
    elif turno == 3:  # De 10:00 pm a 06:00 am
        fin_date = datetime.datetime(l_day_n[0], l_day_n[1], l_day_n[2], 5, 59, 59)

    title_plot = "Variables Robots de Esmaltado turno " + str(turno) + " día " + day

    return ini_date, fin_date, title_plot

@st.cache(persist=False, allow_output_mutation=True, suppress_st_warning=True, show_spinner=True)
def sql_connect(tipo="day", day="2021-04-28", ini="2021-04-27", hour=6, turno=1, server='EASAB101', database='robot1',
                table="robot1", username='IOTVARPROC', password='10Tv4rPr0C2021*'):
    """
    Programa que permite conectar con una base de dato del seervidor y devuelve la base de dato como un pandas dataframe
    INPUT:
        tipo = ["day", "all", "turno", "rango"]
        day = Día inicial EN STR
    OUTPUT:
        pd_sql = pandas dataframe traido de la base de dato SQL
    """

    # Connecting to the sql database
    conn = pyodbc.connect(
        'driver={SQL Server};server=%s;database=%s;uid=%s;pwd=%s' % (server, database, username, password))

    if tipo == "all":
        pd_sql = pd.read_sql_query('SELECT * FROM ' + database + '.dbo.' + table, conn)

        # Saving the sql dataframe to a output file
        now = datetime.datetime.now()
        dt_string = now.strftime("%Y_%m_%d_%H%M")

        #pd_sql.to_csv('./Data/Raw/All_tabla_' + table + '_' + dt_string + '.csv', index=False)
        # pd_sql.to_excel('./Data/Raw/All_tabla_' + table + '_'+ dt_string + '.xlsx', index = False )

    elif tipo == "day":
        pd_sql = pd.read_sql_query("SELECT * FROM " + database + ".dbo." + table + " WHERE fecha like '" + day + "'",
                                   conn)

        # Saving the files
        pd_sql.to_csv('./Data/Raw/tabla_' + table + '_' + day + '.csv', index=False)
        # pd_sql.to_excel('./Data/Raw/tabla_' + table + '_'+ day + '.xlsx', index = False )

    # elif tipo == "hour":
    #    pd_sql = pd.read_sql_query('SELECT TOP '+ str(hour * 3600)   +' * FROM '+database+'.dbo.'+table +
    #                               " WHERE fecha like '" + day+ "'" + ' ORDER BY hora DESC', conn)
    #
    #    # Saving the sql dataframe to a output file
    #    now = datetime.datetime.now()
    #    dt_string = now.strftime("%Y_%m_%d_%H%M")
    #
    #    pd_sql.to_csv('./Data/Raw/tabla_' + table + '_'+ dt_string + '_hour.csv', index = False)
    #    #pd_sql.to_excel('./Data/Raw/tabla_' + table + '_'+ dt_string + '_hour.xlsx', index = False )

    elif tipo == "rango":
        pd_sql = pd.read_sql_query(
            "SELECT * FROM " + database + ".dbo." + table + " WHERE fecha between '" + ini + "'" + " AND '" + day + "'",
            conn)

        # Saving the files
        #pd_sql.to_csv('./Data/Raw/tabla_' + table + '_entre_' + ini + "_y_" + day + '.csv', index=False)
        # pd_sql.to_excel('./Data/Raw/tabla_' + table + '_entre_'+ ini +"_y_"+ day + '.xlsx', index = False )

    elif tipo == "turno":
        ini, day = prev_day(day)

        pd_sql = pd.read_sql_query(
            "SELECT * FROM " + database + ".dbo." + table + " WHERE fecha between '" + ini + "'" + " AND '" + day + "'",
            conn)

        # Saving the files
        #pd_sql.to_csv('./Data/Raw/tabla_' + table + '_' + day + "_turno_" + str(turno) + '.csv', index=False)
        # pd_sql.to_excel('./Data/Raw/tabla_' + table + '_entre_'+ ini +"_y_"+ day + '.xlsx', index = False )

    return pd_sql

@st.cache(persist=False, allow_output_mutation=True, suppress_st_warning=True, show_spinner=True)
def sql_plot(tipo="day", hour=6, turno=1, day="2021-04-28", ini="2021-04-27", database='robot1', table="robot1"):
    """
    Función que se conecta a la base de dato y crea el archivo de visualización a la vez que lo guarda
    INPUT:
        tipo = ["day", "all", "turno", "rango"]
        turno = 1 or 2 or 3
        day = Día inicial EN STR
        ini = Día final EN STR (util cuando el tipo es rango)
    OUTPUT:
        df = pandas dataframe traido de la base de dato SQL
    """
    df = sql_connect(tipo=tipo, day=day, ini=ini, hour=hour, turno=turno, database=database, table=table)
    df = fecha_format(df)
    df["robot"] = table

    # Defining the title and filename for saving the plots
    if tipo == "turno":
        ini_date, fin_date, title = turno_time(day, turno)
        df = df[(df.index >= ini_date) & (df.index <= fin_date)]

        filename = table + '_día_' + day + "_turno_" + str(turno) + '.html'
        title = "Variables " + table + " de Esmaltado Día " + day + " turno " + str(turno)

    elif tipo == "day":
        filename = table + '_día_' + day + '.html'
        title = "Variables " + table + " de Esmaltado Día " + day
    elif tipo == "rango":
        filename = table + '_entre_' + ini + "_y_" + day + '.html'
        title = "Variables " + table + " de Esmaltado entre " + ini + " y " + day

    # Plotting the DF
    fig = plot_html(df, title, filename)
    return df, fig

@st.cache(persist=False, allow_output_mutation=True, suppress_st_warning=True, show_spinner=True)
def sql_plot_all(tipo="day", day="2021-04-28", ini="2021-04-27", hour=6, turno=1):
    """
    Función que se conecta a la base de dato y crea el archivo de visualización a la vez que lo guarda
    INPUT:
        tipo = ["day", "all", "turno", "rango"]
        turno = 1 or 2 or 3
        day = Día inicial EN STR
        ini = Día final EN STR (util cuando el tipo es rango)
    OUTPUT:
        df = pandas dataframe traido de la base de dato SQL del robot 1
        df2 = pandas dataframe traido de la base de dato SQL del robot 2
    """
    df = sql_connect(tipo=tipo, hour=hour, turno=turno, day=day, ini=ini, database="robot1", table="robot1")
    df = fecha_format(df)
    df["robot"] = "robot_1"

    df2 = sql_connect(tipo=tipo, hour=hour, turno=turno, day=day, ini=ini, database="robot2", table="robot2")
    df2 = fecha_format(df2)
    df2["robot"] = "robot_2"

    # Defining the title and filename for saving the plots
    if tipo == "turno":
        ini_date, fin_date, title = turno_time(day, turno)
        df = df[(df.index >= ini_date) & (df.index <= fin_date)]
        df2 = df2[(df2.index >= ini_date) & (df2.index <= fin_date)]

        filename = 'All_Robots_día_' + day + "_turno_" + str(turno) + '.html'
        title = "All Robots día " + day + " turno " + str(turno)

    elif tipo == "day":
        filename = 'All_Robots_día_' + day + '.html'
        title = "Variables Robots de Esmaltado Día " + day
    elif tipo == "rango":
        filename = 'All_Robots_entre_' + ini + "_y_" + day + '.html'
        title = "Variables Robots de Esmaltado entre " + ini + " y " + day

    # Plotting the DF
    fig = plot_html_all(df, df2, title, filename)
    # plot_html_all_2_columns(df, df2, title, filename)

    return df, df2, fig

@st.cache(persist=False, allow_output_mutation=True, suppress_st_warning=True, show_spinner=True)
def sql_plot_presecadero(tipo = "day", day = "2021-04-28", ini ="2021-04-27",  database = 'robot1', table = "robot1"):
    """
    """
    df = sql_connect(tipo = tipo , day = day, ini = ini, database= database, table = table)
    # Organizar el tema de fecha
    df["fecha"] = pd.to_datetime(df['fecha'], format='%Y/%m/%d', exact=False)
    df['fecha'] += pd.to_timedelta(df["hora"], unit='h')
    df['fecha'] += pd.to_timedelta(df["minuto"], unit='m')
    df['fecha'] += pd.to_timedelta(df["segundo"], unit='s')

    # Separar los años, meses y días
    df["año"] = df["fecha"].dt.year
    df["mes"] = df["fecha"].dt.month
    df["dia"] = df["fecha"].dt.day
    df["ndia"] = df["fecha"].dt.day_name()

    # Ordeno la data por la fecha
    df = df.sort_values(by='fecha', ascending=True)

    df.set_index("fecha", inplace=True)
    fig = plot_html_presecadero(df, day)
    return fig

@st.cache(persist=False, allow_output_mutation=True, suppress_st_warning=True, show_spinner=True)
def plot_html(df, title, filename):
    # Create figure with secondary y-axis
    # fig = make_subplots(rows=3, cols=1, specs=[[{"secondary_y": True}]])
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True,  vertical_spacing=0.02,
                        # subplot_titles=('Flujo Masico',  'Presión Atomización')
                        )
    # ----------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------
    # Referencia
    fig.add_trace(go.Scatter(x=df.index, y=df["referencia"],
                             line=dict(color='black', width=1),
                             mode='lines',  # 'lines+markers'
                             name='Referencia'),
                  row=1, col=1,
                  )
    # ----------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------
    # SP_FMASICO
    fig.add_trace(go.Scatter(x=df.index, y=df["sp_fmasico"],
                             line=dict(color='darkorange', width=1, dash='dash'),
                             mode='lines',  # 'lines+markers'
                             name='sp_fmasico'),
                  row=2, col=1,
                  )

    fig.add_trace(go.Scatter(x=df.index, y=df["fmasico"],
                             line=dict(color='steelblue', width=1),
                             mode='lines',  # 'lines+markers'
                             name='fmasico'),
                  secondary_y=False, row=2, col=1)

    # ----------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------
    # SP_PATOMIZACION
    fig.add_trace(go.Scatter(x=df.index, y=df["presion_red"],
                             line=dict(color='silver', width=1),
                             mode='lines', name='Presion Red', legendgroup="Presión red", showlegend=True),
                  secondary_y=False, row=3, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["sp_patomizacion"],
                             line=dict(color='orangered', width=1, dash='dash'),
                             mode='lines', name='sp_patomizacion'),
                  secondary_y=False, row=3, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["patomizacion"],
                             line=dict(color='olivedrab', width=1),
                             mode='lines', name='patomizacion'),
                  secondary_y=False, row=3, col=1)
    # ----------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------
    # SP_PABANICO
    fig.add_trace(go.Scatter(x=df.index, y=df["presion_red"],
                             line=dict(color='silver', width=1),
                             mode='lines', name='Presion Red', legendgroup="Presión red", showlegend=False),
                  secondary_y=False, row=4, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["sp_pabanico"],
                             line=dict(color='grey', width=1, dash='dash'),
                             mode='lines', name='sp_pabanico'),
                  secondary_y=False, row=4, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["pabanico"],
                             line=dict(color='teal', width=1),
                             mode='lines', name='pabanico'),
                  secondary_y=False, row=4, col=1)

    # Add figure title
    fig.update_layout(height=1000, title=title)

    # Template
    fig.layout.template = 'seaborn'  # ggplot2, plotly_dark, seaborn, plotly, plotly_white

    # Set x-axis and y-axis title
    # fig.update_xaxes(title = "xaxis title")
    # fig['layout']['xaxis']['title']='Tiempo'
    fig['layout']['xaxis4']['title'] = 'Fecha'
    fig['layout']['yaxis']['title'] = 'Referencia'
    fig['layout']['yaxis2']['title'] = 'Flujo Masico'
    fig['layout']['yaxis3']['title'] = 'P Atomización'
    fig['layout']['yaxis4']['title'] = 'P Abanico'

    # Set y-axes titles
    # fig.update_yaxes(title_text="<b>Variables</b> yaxis title", secondary_y=False)
    # fig.update_yaxes(title_text="<b>Descarga Derivada</b> yaxis title", secondary_y=True)

    #st.plotly_chart(fig, use_container_width=True)

    #fig.show()

    #plotly.offline.plot(fig, filename=filename, auto_open=False)

    return fig

@st.cache(persist=False, allow_output_mutation=True, suppress_st_warning=True, show_spinner=True)
def plot_html_all(df, df2, title_plot, filename):
    """
    Funcion para dibujar los 2 robots en 1 misma grafica
    """

    # Create figure with secondary y-axis
    # fig = make_subplots(rows=3, cols=1, specs=[[{"secondary_y": True}]])
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.02,
                        # subplot_titles=('Flujo Masico',  'Presión Atomización')
                        )

    # Referencia
    fig.add_trace(go.Scatter(x=df.index, y=df["referencia"],
                             line=dict(color='black', width=1),
                             mode='lines',  # 'lines+markers'
                             name='Referencia 1', legendgroup="Ref", showlegend=True),
                  row=1, col=1,
                  )
    # ----------------------------------------------------------------------------------------------------------
    fig.add_trace(go.Scatter(x=df.index, y=df2["referencia"],
                             line=dict(color='silver', width=1),
                             mode='lines',  # 'lines+markers'
                             name='Referencia 2', legendgroup="Ref2", showlegend=True),
                  row=1, col=1,
                  )
    # ----------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------
    # SP_FMASICO
    fig.add_trace(go.Scatter(x=df.index, y=df["sp_fmasico"],
                             line=dict(color='darkorange', width=1, dash='dash'),
                             mode='lines',  # 'lines+markers'
                             name='sp_fmasico 1', legendgroup="Ref", showlegend=True),
                  row=2, col=1,
                  )

    fig.add_trace(go.Scatter(x=df.index, y=df["fmasico"],
                             line=dict(color='steelblue', width=1),
                             mode='lines',  # 'lines+markers'
                             name='fmasico 1', legendgroup="Ref", showlegend=True),
                  secondary_y=False, row=2, col=1)
    # ----------------------------------------------------------------------------------------------------------
    fig.add_trace(go.Scatter(x=df.index, y=df2["sp_fmasico"],
                             line=dict(color='grey', width=1, dash='dash'),
                             mode='lines',  # 'lines+markers'
                             name='sp_fmasico 2', legendgroup="Ref2", showlegend=True),
                  row=2, col=1,
                  )

    fig.add_trace(go.Scatter(x=df.index, y=df2["fmasico"],
                             line=dict(color='olivedrab', width=1),
                             mode='lines',  # 'lines+markers'
                             name='fmasico 2', legendgroup="Ref2", showlegend=True),
                  secondary_y=False, row=2, col=1)
    # ----------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------
    # SP_PATOMIZACION
    fig.add_trace(go.Scatter(x=df.index, y=df["presion_red"],
                             line=dict(color='black', width=1),
                             mode='lines', name='Presion Red 1', legendgroup="Ref", showlegend=True),
                  secondary_y=False, row=3, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["sp_patomizacion"],
                             line=dict(color='darkorange', width=1, dash='dash'),
                             mode='lines', name='sp_patomizacion 1', legendgroup="Ref", showlegend=True),
                  secondary_y=False, row=3, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["patomizacion"],
                             line=dict(color='steelblue', width=1),
                             mode='lines', name='patomizacion 1', legendgroup="Ref", showlegend=True),
                  secondary_y=False, row=3, col=1)

    # ----------------------------------------------------------------------------------------------------------
    fig.add_trace(go.Scatter(x=df.index, y=df2["presion_red"],
                             line=dict(color='silver', width=1),
                             mode='lines', name='Presion Red 2', legendgroup="Ref2", showlegend=True),
                  secondary_y=False, row=3, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df2["sp_patomizacion"],
                             line=dict(color='grey', width=1, dash='dash'),
                             mode='lines', name='sp_patomizacion 2', legendgroup="Ref2", showlegend=True),
                  secondary_y=False, row=3, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df2["patomizacion"],
                             line=dict(color='olivedrab', width=1),
                             mode='lines', name='patomizacion 2', legendgroup="Ref2", showlegend=True),
                  secondary_y=False, row=3, col=1)
    # ----------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------
    # SP_PABANICO
    fig.add_trace(go.Scatter(x=df.index, y=df["sp_pabanico"],
                             line=dict(color='darkorange', width=1, dash='dash'),
                             mode='lines', name='sp_pabanico 1', legendgroup="Ref", showlegend=True),
                  secondary_y=False, row=4, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["pabanico"],
                             line=dict(color='steelblue', width=1),
                             mode='lines', name='pabanico 1', legendgroup="Ref", showlegend=True),
                  secondary_y=False, row=4, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["presion_red"],
                             line=dict(color='black', width=1),
                             mode='lines', name='Presion Red 1', legendgroup="Ref", showlegend=False),
                  secondary_y=False, row=4, col=1)
    # ----------------------------------------------------------------------------------------------------------
    fig.add_trace(go.Scatter(x=df.index, y=df2["sp_pabanico"],
                             line=dict(color='grey', width=1, dash='dash'),
                             mode='lines', name='sp_pabanico 2', legendgroup="Ref2", showlegend=True),
                  secondary_y=False, row=4, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df2["pabanico"],
                             line=dict(color='olivedrab', width=1),
                             mode='lines', name='pabanico 2', legendgroup="Ref2", showlegend=True),
                  secondary_y=False, row=4, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df2["presion_red"],
                             line=dict(color='silver', width=1),
                             mode='lines', name='Presion Red 2', legendgroup="Ref2", showlegend=False),
                  secondary_y=False, row=4, col=1)
    # ----------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------

    # Add figure title
    fig.update_layout(height=1000, title=title_plot, legend=dict(orientation="v", ))
    # yanchor="bottom",
    # y=0,
    # xanchor="right",
    # x=0
    # )
    # )

    # Template
    fig.layout.template = 'seaborn'  # ggplot2, plotly_dark, seaborn, plotly, plotly_white

    # Set x-axis and y-axis title
    # fig.update_xaxes(title = "xaxis title")
    # fig['layout']['xaxis']['title']='Tiempo'
    fig['layout']['xaxis4']['title'] = 'Fecha'
    fig['layout']['yaxis']['title'] = 'Referencia'
    fig['layout']['yaxis2']['title'] = 'Flujo Masico'
    fig['layout']['yaxis3']['title'] = 'P Atomización'
    fig['layout']['yaxis4']['title'] = 'P Abanico'

    # Set y-axes titles
    # fig.update_yaxes(title_text="<b>Variables</b> yaxis title", secondary_y=False)
    # fig.update_yaxes(title_text="<b>Descarga Derivada</b> yaxis title", secondary_y=True)

    #st.plotly_chart(fig, use_container_width=True)

    #fig.show())

    #plotly.offline.plot(fig, filename=filename, auto_open=False)

    return fig

@st.cache(persist=False, allow_output_mutation=True, suppress_st_warning=True, show_spinner=True)
def plot_html_presecadero(df, day):
    # Create figure with secondary y-axis
    # fig = make_subplots(rows=3, cols=1, specs=[[{"secondary_y": True}]])
    fig = make_subplots(rows=1, cols=1, shared_xaxes=True, vertical_spacing=0.02,
                        # subplot_titles=('Flujo Masico',  'Presión Atomización')
                        )

    # Sp_temp_zona_1
    fig.add_trace(go.Scatter(x=df.index, y=df["Sp_temp_Z1"],
                             line=dict(color='darkorange', width=1, dash='dash'),
                             mode='lines',  # 'lines+markers'
                             name='Sp_temp_zona_1'),
                  row=1, col=1,
                  )

    fig.add_trace(go.Scatter(x=df.index, y=df["temp_Z1"],
                             line=dict(color='steelblue', width=1),
                             mode='lines',  # 'lines+markers'
                             name='temp_zona_1'),
                  secondary_y=False, row=1, col=1)

    # Sp_temp_zona_2
    fig.add_trace(go.Scatter(x=df.index, y=df["temp_Z2"],
                             line=dict(color='orangered', width=1, dash='dash'),
                             mode='lines', name='temp_zona_2'),
                  secondary_y=False, row=1, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["temp_Z3"],
                             line=dict(color='olivedrab', width=1),
                             mode='lines', name='temp_zona_3'),
                  secondary_y=False, row=1, col=1)

    # fig.add_trace(go.Scatter(x=df.index, y=df["Sp_HR_Z1"],
    #                    line=dict(color='olivedrab', width=1),
    #                    mode='lines', name='sp_HR_Z1'),
    #                    secondary_y = False, row = 2, col = 1)
    #
    # Add figure title
    fig.update_layout(height=500, title="Pre-secadero")

    # Template
    fig.layout.template = 'seaborn'  # ggplot2, plotly_dark, seaborn, plotly, plotly_white

    # Set x-axis and y-axis title
    # fig.update_xaxes(title = "xaxis title")
    # fig['layout']['xaxis']['title']='Tiempo'
    fig['layout']['xaxis']['title'] = 'Fecha'
    fig['layout']['yaxis']['title'] = 'Temp_Zonas'
    # fig['layout']['yaxis2']['title']='HR'

    # Set y-axes titles
    # fig.update_yaxes(title_text="<b>Variables</b> yaxis title", secondary_y=False)
    # fig.update_yaxes(title_text="<b>Descarga Derivada</b> yaxis title", secondary_y=True)
    #st.plotly_chart(fig, use_container_width=True)

    #fig.show()

    #plotly.offline.plot(fig, filename='Pre-secadero_Variables_' + day + '.html', auto_open=False)

    return fig

@st.cache(persist=False, allow_output_mutation=True, suppress_st_warning=True, show_spinner=True)
def Round(x):
    return np.round(x,3)

@st.cache(persist=False, allow_output_mutation=True, suppress_st_warning=True, show_spinner=True)
def DF_Analitica_Esmalte(df):
    """
    Programa que analisa la serie de tiempo y crea un df con data de cada proceso de esmaltado
    """
    # Inicialización del DF
    Analisis_df = pd.DataFrame(columns=["Fecha", "Día", "Turno", "Hora", "Robot", "Proceso_Completo",
                                        "Referencia", "Tiempo_Estado [s]", "Tiempo_Esmaltado [s]",
                                        "Tiempo_Esmaltado_SP [s]",
                                        "Esmalte_Usado [Kg]", "Esmalte_Usado_SP [Kg]", "Diff_Esmalte [gr]",
                                        "Max_Fmasico [gr/min]",
                                        "Promedio_Fmasico [gr/min]", "Promedio_SP_Fmasico [gr/min]",
                                        "Desviación_max_Fmasico [gr/min]", "Peso_Antes [Kg]", "Peso_Despues [kg]",
                                        "Max_Presión_Red [psi]", "Min_Presión_Red [psi]", "Promedio_Presión_Red [psi]",
                                        "Max_Presión_Atomización [psi]", "Promedio_Presión_Atomización [psi]",
                                        "Promedio_SP_Presión_Atomización [psi]", "Desviación_Presión_Atomización [psi]",
                                        "Max_Presión_Abanico [psi]", "Promedio_Presión_Abanico [psi]",
                                        "Promedio_SP_Presión_Abanico [psi]", "Desviación_Presión_Abanico [psi]",
                                        "Fecha_planta"])

    # Inicialización de variables
    count = 0
    idx = 0
    pre = 3

    while idx < df.shape[0]:

        # -------------------------------------------------------------------------------
        # Inicializacion varibles
        # -------------------------------------------------------------------------------
        # Tiempos de conteo del proceso
        tiempo_estado = 0
        tiempo_fmasico = 0
        tiempo_sp_fmasico = 0
        tiempo_patomizacion = 0
        tiempo_sp_patomizacion = 0
        tiempo_pabanico = 0
        tiempo_sp_pabanico = 0

        # Flujo masico y set point flujo masico y desviacion flujo masico
        flujo_masico_total = 0
        max_flujo_masico = 0
        sp_flujo_masico_total = 0
        desv_flujo_masico_max = 0

        # Presion de red
        Max_Pred = 0
        Min = 0
        Total_Pred = 0

        # Presion Atomización
        total_patomizacion = 0
        max_patomizacion = 0
        total_sp_patomizacion = 0

        # Presion Abanico
        total_pabanico = 0
        max_pabanico = 0
        total_sp_pabanico = 0

        #  Flag de control de entradas y ciclos
        flag_comp = 1
        flag_fmasico = True
        flag_sp_fmasico = True

        flag_patomizacion = True
        flag_sp_patomizacion = True
        flag_pabanico = True
        flag_sp_pabanico = True
        # -------------------------------------------------------------------------------
        # ESTADO ENCENDIDO
        # -------------------------------------------------------------------------------
        if df.iloc[idx]['estado'] == 1:

            # Guardo la fecha de inicio del esmaltado, la referencia y el robot
            fecha_ini = df.index[idx].date()
            fecha_proceso = df.iloc[idx]["fecha_planta"].date()
            referencia_esmaltada = df.iloc[idx]['referencia']
            robot = df.iloc[idx]["robot"]

            # Guardo el dia, la hora y el turno
            ndia = df.iloc[idx]["ndia"]
            hora = df.index[idx].time()
            turno = np.floor((df.index[idx] - datetime.timedelta(hours=6)).time().hour / 8) + 1

            # Guardo el peso antes y peso despues OJO AQUI HAY UN ERROR
            peso_antes = df.iloc[idx]["peso_antes"]
            peso_despues = df.iloc[idx]["peso_despues"]

            # Inicializar Presion de referencia minima
            Min_Pred = df.iloc[idx]["presion_red"]

            # --------------------------------------------------------------------------------------------
            # Recorro el proceso mientras el estado sea activo
            while df.iloc[idx]['estado'] == 1:
                # Cuento el tiempo que estado permanecio on
                tiempo_estado += 1

                # --------------------------------------------------------------------------------------------
                # Calcular LA PRESION DE RED
                if Max_Pred < df.iloc[idx]["presion_red"]:
                    Max_Pred = df.iloc[idx]["presion_red"]

                if Min_Pred > df.iloc[idx]["presion_red"]:
                    Min_Pred = df.iloc[idx]["presion_red"]

                Total_Pred += df.iloc[idx]["presion_red"]

                # --------------------------------------------------------------------------------------------
                # Calcular la desviación del flujo masico vs la del set point
                # desv_flujo_masico_aux = abs((df.iloc[idx]["fmasico"] - df.iloc[idx]["sp_fmasico"])/60)
                #
                # if desv_flujo_masico_aux > abs(desv_flujo_masico_max):
                #    desv_flujo_masico_max = (df.iloc[idx]["fmasico"] - df.iloc[idx]["sp_fmasico"])/60

                # --------------------------------------------------------------------------------------------
                # Conteo del flujo masico
                if df.iloc[idx]['fmasico'] > 0 and flag_fmasico == True:
                    idx_fmasico = idx

                    while df.iloc[idx_fmasico]['fmasico'] > 0 or df.iloc[idx_fmasico + 1]['fmasico'] > 0:

                        # Acumulo la data del proceso
                        tiempo_fmasico += 1
                        flujo_masico_total += df.iloc[idx_fmasico]["fmasico"] / 60 / 1000

                        # Maximo del flujo maxico
                        if max_flujo_masico < df.iloc[idx_fmasico]["fmasico"]:
                            max_flujo_masico = df.iloc[idx_fmasico]["fmasico"]

                        # Avanzo en el df
                        idx_fmasico += 1

                        # Por si el df finaliza o inicia con el estado 1, es decir que se corto el proceso
                        if idx_fmasico >= df.shape[0]:
                            flag_comp = 0
                            print(
                                "¡NO SE TIENEN DATOS SUFICIENTE DE LA ULTIMA PIEZA ESMALTADA: El proceso no ha finalizado!\n")
                            break  # Salir del ciclo para evitar un error
                        elif idx_fmasico - 1 == 0:
                            flag_comp = 0
                            print(
                                "¡NO SE TIENEN DATOS SUFICIENTE DE LA PRIMERA PIEZA ESMALTADA: El proceso no ha finalizado!\n")

                    # Flag para no volver a entrar
                    flag_fmasico = False

                # --------------------------------------------------------------------------------------------
                # Conteo del Set point flujo masico
                if df.iloc[idx]['sp_fmasico'] > 0 and flag_sp_fmasico == True:
                    idx_fmasico = idx

                    while df.iloc[idx_fmasico]['sp_fmasico'] > 0 or df.iloc[idx_fmasico + 1]['sp_fmasico'] > 0:

                        # Acumulo la data del proceso
                        tiempo_sp_fmasico += 1
                        sp_flujo_masico_total += df.iloc[idx_fmasico]["sp_fmasico"] / 60 / 1000

                        # Avanzo en el df
                        idx_fmasico += 1

                        # Por si el df finaliza o inicia con el estado 1, es decir que se corto el proceso
                        if idx_fmasico >= df.shape[0]:
                            flag_comp = 0
                            # print("¡NO SE TIENEN DATOS SUFICIENTE DE LA ULTIMA PIEZA ESMALTADA: El proceso no ha finalizado!\n")
                            break  # Salir del ciclo para evitar un error
                        elif idx_fmasico - 1 == 0:
                            flag_comp = 0
                            # print("¡NO SE TIENEN DATOS SUFICIENTE DE LA PRIMERA PIEZA ESMALTADA: El proceso no ha finalizado!\n")

                    # Flag para no volver a entrar
                    flag_sp_fmasico = False

                # --------------------------------------------------------------------------------------------
                # Conteo del Presion Atomizacion
                if df.iloc[idx]['patomizacion'] > 0 and flag_patomizacion == True:
                    idx_fmasico = idx

                    while df.iloc[idx_fmasico]['patomizacion'] > 0 or df.iloc[idx_fmasico + 1]['patomizacion'] > 0:

                        # Acumulo la data del proceso
                        tiempo_patomizacion += 1
                        total_patomizacion += df.iloc[idx_fmasico]["patomizacion"]

                        # Maximo de la presion de atomizacion
                        if max_patomizacion < df.iloc[idx_fmasico]["patomizacion"]:
                            max_patomizacion = df.iloc[idx_fmasico]["patomizacion"]

                        # Avanzo en el df
                        idx_fmasico += 1

                        # Por si el df finaliza o inicia con el estado 1, es decir que se corto el proceso
                        if idx_fmasico >= df.shape[0]:
                            flag_comp = 0
                            # print("¡NO SE TIENEN DATOS SUFICIENTE DE LA ULTIMA PIEZA ESMALTADA: El proceso no ha finalizado!\n")
                            break  # Salir del ciclo para evitar un error
                        elif idx_fmasico - 1 == 0:
                            flag_comp = 0
                            # print("¡NO SE TIENEN DATOS SUFICIENTE DE LA PRIMERA PIEZA ESMALTADA: El proceso no ha finalizado!\n")

                    # Flag para no volver a entrar
                    flag_patomizacion = False
                # --------------------------------------------------------------------------------------------
                # Conteo del  set_point -Presion Atomizacion
                if df.iloc[idx]['sp_patomizacion'] > 0 and flag_sp_patomizacion == True:
                    idx_fmasico = idx

                    while df.iloc[idx_fmasico]['sp_patomizacion'] > 0 or df.iloc[idx_fmasico + 1][
                        'sp_patomizacion'] > 0:

                        # Acumulo la data del proceso
                        tiempo_sp_patomizacion += 1
                        total_sp_patomizacion += df.iloc[idx_fmasico]["sp_patomizacion"]

                        ##Maximo de la presion de atomizacion
                        # if max_patomizacion < df.iloc[idx_fmasico]["sp_patomizacion"]:
                        #    max_patomizacion = df.iloc[idx_fmasico]["sp_patomizacion"]

                        # Avanzo en el df
                        idx_fmasico += 1

                        # Por si el df finaliza o inicia con el estado 1, es decir que se corto el proceso
                        if idx_fmasico >= df.shape[0]:
                            flag_comp = 0
                            # print("¡NO SE TIENEN DATOS SUFICIENTE DE LA ULTIMA PIEZA ESMALTADA: El proceso no ha finalizado!\n")
                            break  # Salir del ciclo para evitar un error
                        elif idx_fmasico - 1 == 0:
                            flag_comp = 0
                            # print("¡NO SE TIENEN DATOS SUFICIENTE DE LA PRIMERA PIEZA ESMALTADA: El proceso no ha finalizado!\n")

                    # Flag para no volver a entrar
                    flag_sp_patomizacion = False

                # --------------------------------------------------------------------------------------------
                # Conteo del Presion abanico
                if df.iloc[idx]['pabanico'] > 0 and flag_pabanico == True:
                    idx_fmasico = idx

                    while df.iloc[idx_fmasico]['pabanico'] > 0 or df.iloc[idx_fmasico + 1]['pabanico'] > 0:

                        # Acumulo la data del proceso
                        tiempo_pabanico += 1
                        total_pabanico += df.iloc[idx_fmasico]["pabanico"]

                        # Maximo de la presion de atomizacion
                        if max_pabanico < df.iloc[idx_fmasico]["pabanico"]:
                            max_pabanico = df.iloc[idx_fmasico]["pabanico"]

                        # Avanzo en el df
                        idx_fmasico += 1

                        # Por si el df finaliza o inicia con el estado 1, es decir que se corto el proceso
                        if idx_fmasico >= df.shape[0]:
                            flag_comp = 0
                            # print("¡NO SE TIENEN DATOS SUFICIENTE DE LA ULTIMA PIEZA ESMALTADA: El proceso no ha finalizado!\n")
                            break  # Salir del ciclo para evitar un error
                        elif idx_fmasico - 1 == 0:
                            flag_comp = 0
                            # print("¡NO SE TIENEN DATOS SUFICIENTE DE LA PRIMERA PIEZA ESMALTADA: El proceso no ha finalizado!\n")

                    # Flag para no volver a entrar
                    flag_pabanico = False
                # --------------------------------------------------------------------------------------------
                # Conteo del  set_point -Presion abanico
                if df.iloc[idx]['sp_pabanico'] > 0 and flag_sp_pabanico == True:
                    idx_fmasico = idx

                    while df.iloc[idx_fmasico]['sp_pabanico'] > 0 or df.iloc[idx_fmasico + 1]['sp_pabanico'] > 0:

                        # Acumulo la data del proceso
                        tiempo_sp_pabanico += 1
                        total_sp_pabanico += df.iloc[idx_fmasico]["sp_pabanico"]

                        ##Maximo de la presion de atomizacion
                        # if max_patomizacion < df.iloc[idx_fmasico]["sp_pabanico"]:
                        #    max_patomizacion = df.iloc[idx_fmasico]["sp_pabanico"]

                        # Avanzo en el df
                        idx_fmasico += 1

                        # Por si el df finaliza o inicia con el estado 1, es decir que se corto el proceso
                        if idx_fmasico >= df.shape[0]:
                            flag_comp = 0
                            # print("¡NO SE TIENEN DATOS SUFICIENTE DE LA ULTIMA PIEZA ESMALTADA: El proceso no ha finalizado!\n")
                            break  # Salir del ciclo para evitar un error
                        elif idx_fmasico - 1 == 0:
                            flag_comp = 0
                            # print("¡NO SE TIENEN DATOS SUFICIENTE DE LA PRIMERA PIEZA ESMALTADA: El proceso no ha finalizado!\n")

                    # Flag para no volver a entrar
                    flag_sp_pabanico = False
                # --------------------------------------------------------------------------------------------
                # Avanzo en el df
                idx += 1

                # Por si el df finaliza o inicia con el estado 1, es decir que se corto el proceso
                if idx >= df.shape[0]:
                    flag_comp = 0
                    # print("¡NO SE TIENEN DATOS SUFICIENTE DE LA ULTIMA PIEZA ESMALTADA: El proceso no ha finalizado!\n")
                    break  # Salir del ciclo para evitar un error
                elif idx - 1 == 0:
                    flag_comp = 0
                    # print("¡NO SE TIENEN DATOS SUFICIENTE DE LA PRIMERA PIEZA ESMALTADA: El proceso no ha finalizado!\n")

            # -------------------------------------------------------------------------------------------------------------
            # Evitando la division por cero cuando el estado esta ON pero no sale flujo ni presión
            # -------------------------------------------------------------------------------------------------------------
            if tiempo_fmasico == 0:
                tiempo_fmasico = tiempo_sp_fmasico
                if tiempo_fmasico == 0:
                    tiempo_fmasico = 1
                    tiempo_sp_fmasico = 1
                # tiempo_fmasico = tiempo_estado
                print("Tiempo fmasico ", tiempo_fmasico)
                print(hora)

            if tiempo_patomizacion == 0:
                tiempo_patomizacion = tiempo_sp_patomizacion
                if tiempo_patomizacion == 0:
                    tiempo_patomizacion = 1
                    tiempo_sp_patomizacion = 1
                # tiempo_patomizacion = tiempo_estado
                print("Tiempo patomizacion ", tiempo_patomizacion)
                print(hora)

            if tiempo_pabanico == 0:
                tiempo_pabanico = tiempo_sp_pabanico
                if tiempo_pabanico == 0:
                    tiempo_pabanico = 1
                    tiempo_sp_pabanico = 1
                # tiempo_pabanico = tiempo_estado
                print("Tiempo pabanico ", tiempo_pabanico)
                print(hora)

            # -------------------------------------------------------------------------------------------------------------
            # Llenando los datos del DF analisis
            # -------------------------------------------------------------------------------------------------------------
            desv_flujo_masico_max = max_flujo_masico - (((sp_flujo_masico_total * 1000) / tiempo_sp_fmasico) * 60)

            Analisis_df.loc[count] = [fecha_ini, ndia, turno, hora, robot, float(flag_comp), referencia_esmaltada,float(tiempo_estado),
                                      float(tiempo_fmasico), float(tiempo_sp_fmasico),
                                      Round(flujo_masico_total), Round(sp_flujo_masico_total),
                                      Round((flujo_masico_total - sp_flujo_masico_total)* 1000),
                                      Round(max_flujo_masico),
                                      Round(((flujo_masico_total * 1000) / tiempo_fmasico)*60),
                                      Round(((sp_flujo_masico_total * 1000) / tiempo_sp_fmasico)*60), #[gr/min]
                                      Round(desv_flujo_masico_max), peso_antes, peso_despues,
                                      Max_Pred, Min_Pred, Round((Total_Pred/ tiempo_estado)),
                                      max_patomizacion, Round((total_patomizacion/tiempo_patomizacion)),
                                      Round((total_sp_patomizacion/tiempo_sp_patomizacion)),
                                      Round((total_patomizacion/tiempo_patomizacion)- (total_sp_patomizacion/tiempo_sp_patomizacion)),
                                      max_pabanico, Round((total_pabanico/tiempo_pabanico)),
                                      Round((total_sp_pabanico/tiempo_sp_pabanico)),
                                      Round((total_pabanico/tiempo_pabanico)- (total_sp_pabanico/tiempo_sp_pabanico)),
                                      fecha_proceso]

            # Cuento la referencia esmaltada
            count += 1

        else:
            # Avanzo en el df
            idx += 1

    #print("Se han esmaltado %i piezas" % count)

    return Analisis_df
# ----------------------------------------------------------------------------------------------------------------------
# Importing the DataFrame
st.title(' 📈 IIOT - Corona 🤖')

if page == "Celula de Esmaltado":
    st.header('Celula Robotizada de Esmaltado Girardota')
    st.subheader("1. Selección de Data a Analizar")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Opciones de Fecha**")
        sel_fecha = st.radio("¿Que periodo de tiempo desea analizar?",
                             ('Por día', 'Por rango de días'), key="fecha")
        if sel_fecha == "Por día":
            sel_dia = st.date_input("¿Que dia desea analizar?", datetime.date.today(), key="dia")
            if sel_dia > datetime.date.today():
                st.error("Recuerda que el día seleccionado no puede ser superior al día actual")
                st.stop()
            st.info("Analizaras el día " + str(sel_dia))
        elif sel_fecha == "Por rango de días":
            sel_dia_ini = st.date_input("Seleccione el día inicial", datetime.date.today() -
                                        datetime.timedelta(days=1), key="dia_ini")
            sel_dia_fin = st.date_input("Seleccione el día final", datetime.date.today(), key="dia_fin")

            if sel_dia_fin <= sel_dia_ini:
                st.error("Recuerda seleccionar una fecha inicial anterior a la fecha final!!!")
                st.stop()
            elif sel_dia_fin > datetime.date.today():
                st.error("Recuerda que la fecha final no puede ser superior a la fecha actual")
                st.stop()
            else:
                st.info("Analizaras un periodo de tiempo de " + str((sel_dia_fin - sel_dia_ini).days +1 ) + " días." )
    with col2:
        st.markdown("**Selección del Robot**")
        sel_robot = st.radio( "¿Que Robot desea analizar?",
                              ('Robot 1', 'Robot 2', 'Ambos'), key="robot")

    st.subheader("2. Descargar y Graficar Información")
    if st.checkbox("Descargar y Graficar Información"):
        with st.spinner('Descargando la información y dibujandola...'):
            if sel_fecha == "Por día":
                if sel_robot == "Robot 1":
                    df, fig = sql_plot(tipo="day", day=str(sel_dia), database='robot1', table="robot1")
                    st.plotly_chart(fig, use_container_width=True)
                elif sel_robot == "Robot 2":
                    df, fig = sql_plot(tipo="day", day=str(sel_dia), database='robot2', table="robot2")
                    st.plotly_chart(fig, use_container_width=True)
                elif sel_robot == "Ambos":
                    robot1, robot2, fig = sql_plot_all(tipo="day", day=str(sel_dia))
                    st.plotly_chart(fig, use_container_width=True)
            elif sel_fecha == "Por rango de días":
                if sel_robot == "Robot 1":
                    df, fig= sql_plot(tipo = "rango", ini = str(sel_dia_ini), day = str(sel_dia_fin),
                                  database = 'robot1', table = "robot1")
                    st.plotly_chart(fig, use_container_width=True)
                elif sel_robot == "Robot 2":
                    df, fig = sql_plot(tipo = "rango", ini = str(sel_dia_ini), day = str(sel_dia_fin),
                                  database = 'robot2', table = "robot2")
                    st.plotly_chart(fig, use_container_width=True)
                elif sel_robot == "Ambos":
                    robot1, robot2, fig = sql_plot_all(tipo = "rango", ini = str(sel_dia_ini), day = str(sel_dia_fin))
                    st.plotly_chart(fig, use_container_width=True)

        st.subheader("3. Analizar Información")
        if st.checkbox("Analizar", key="Analizar"):
            with st.spinner('Analizando la información...'):
                if sel_robot == "Robot 1" or sel_robot == "Robot 2":
                    Analisis_df = DF_Analitica_Esmalte(df)
                elif sel_robot == "Ambos":
                    Analisis_df1 = DF_Analitica_Esmalte(robot1)
                    Analisis_df2 = DF_Analitica_Esmalte(robot2)
                    Analisis_df = pd.concat([Analisis_df1, Analisis_df2])

                gb = GridOptionsBuilder.from_dataframe(Analisis_df)
                #gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
                gb.configure_side_bar()
                gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc="sum",
                                            editable=False)
                gridOptions = gb.build()

                tabla = AgGrid(Analisis_df,
                               editable=False,
                               sortable=True,
                               filter=True,
                               resizable=True,
                               defaultWidth=5,
                               fit_columns_on_grid_load=False,
                               theme="streamlit",  # "light", "dark", "blue", "fresh", "material"
                               key='analisis_table',
                               reload_data=True,
                               gridOptions=gridOptions, enable_enterprise_modules=True
                               )

            st.subheader("4. Reportes Consumos y Cantidades")
            # Reportes de las tablas dinamicas pre-establecidas
            if st.checkbox("Reportes Pre-Establecidos"):
                # Tablas dinamicas
                cantidad_piezas = Analisis_df.pivot_table(index=["Fecha_planta", "Robot", "Turno"], values="Proceso_Completo",
                                                        columns="Referencia", aggfunc='sum', fill_value=0, margins=False)

                cantidad_piezas_grap = Analisis_df.pivot_table(index=["Fecha_planta", "Robot"], values="Proceso_Completo",
                                                             columns="Referencia", aggfunc='sum',
                                                             fill_value=0, margins=False).reset_index()

                horas_piezas = Analisis_df.pivot_table(index=["Fecha_planta", "Robot", "Turno"], values="Tiempo_Estado [s]",
                                                     columns="Referencia", aggfunc='sum', fill_value=0, margins=False) / 3600

                esmalte_cons = Analisis_df.pivot_table(index=["Fecha_planta", "Robot", "Turno"], values="Esmalte_Usado [Kg]",
                                                     columns="Referencia", aggfunc='sum', fill_value=0, margins=False)
                esmalte_cons_grap = Analisis_df.pivot_table(index=["Fecha_planta", "Robot"], values="Esmalte_Usado [Kg]",
                                                          columns="Referencia", aggfunc='sum', fill_value=0,
                                                          margins=False).reset_index()

                st.markdown("**Cantidad de Piezas Esmaltadas**")
                st.write("Cantidad de piezas esmaltadas por referencía, día, robot y turno.")
                cantidad_piezas = cantidad_piezas.reset_index()

                # Show Table
                # All columns to string to ve able to use aggrid
                cantidad_piezas.columns = list(map(str,cantidad_piezas.columns.values.tolist()))

                gb = GridOptionsBuilder.from_dataframe(cantidad_piezas)
                #gb.configure_pagination(paginationAutoPageSize=True, paginationPageSize=10)
                gb.configure_side_bar()
                gridOptions = gb.build()

                AgGrid(cantidad_piezas,editable=False, sortable=True,filter=True,resizable=True,defaultWidth=5,
                       fit_columns_on_grid_load=False,theme="streamlit",  # "light", "dark", "blue", "fresh", "material"
                       key='cantidad_piezas',reload_data=True,
                       gridOptions=gridOptions, enable_enterprise_modules=True
                       )

                st.markdown("**Horas Totales Trabajadas**")
                st.write("Cantidad de Horas activas de la maquina por referencía, día, robot y turno.")
                horas_piezas = horas_piezas.reset_index()

                # Show Table
                # All columns to string to ve able to use aggrid
                horas_piezas.columns = list(map(str,horas_piezas.columns.values.tolist()))

                gb = GridOptionsBuilder.from_dataframe(horas_piezas)
                #gb.configure_pagination(paginationAutoPageSize=True, paginationPageSize=10)
                gb.configure_side_bar()
                gridOptions = gb.build()

                AgGrid(horas_piezas.round(2),editable=False, sortable=True,filter=True,resizable=True,defaultWidth=5,
                       fit_columns_on_grid_load=False,theme="streamlit",  # "light", "dark", "blue", "fresh", "material"
                       key='horas_piezas',reload_data=True,
                       gridOptions=gridOptions, enable_enterprise_modules=True
                       )

                st.markdown("**Cantidad de Esmalte Consumido**")
                st.write("Cantidad de esmalte utilizado por referencía, día, robot y turno.")
                esmalte_cons = esmalte_cons.reset_index()

                # Show Table
                # All columns to string to ve able to use aggrid
                esmalte_cons.columns = list(map(str,esmalte_cons.columns.values.tolist()))

                gb = GridOptionsBuilder.from_dataframe(esmalte_cons)
                #gb.configure_pagination(paginationAutoPageSize=True, paginationPageSize=10)
                gb.configure_side_bar()
                gridOptions = gb.build()

                AgGrid(esmalte_cons.round(2),editable=False, sortable=True,filter=True,resizable=True,defaultWidth=5,
                       fit_columns_on_grid_load=False,theme="streamlit",  # "light", "dark", "blue", "fresh", "material"
                       key='esmalte_cons',reload_data=True,
                       gridOptions=gridOptions, enable_enterprise_modules=True
                       )

                with st.expander("Ver graficas"):
                    p1, p2 = st.columns(2)
                    iter_colum = cantidad_piezas_grap.columns.values.tolist()[2:]
                # -------------------------------------Plotly-----------------------------------------------------------
                    fig = go.Figure()
                    for elem in iter_colum:
                        fig.add_trace(go.Bar(
                            x=cantidad_piezas_grap["Fecha_planta"],
                            y=cantidad_piezas_grap[int(elem)],
                            #text=cantidad_piezas_grap[int(elem)],textposition='auto',
                            name=elem))

                    # Here we modify the tickangle of the xaxis, resulting in rotated labels.
                    fig.update_layout(barmode='group', bargap=0.1,  bargroupgap=0.02, xaxis_tickangle=0)
                    fig.update_layout(height=500, width=700, legend=dict(orientation="v"))
                    fig.update_layout(template="seaborn", title="Cantidad de Piezas Esmaltadas")

                    # Set x-axis and y-axis title
                    fig['layout']['xaxis']['title'] = 'Fecha'
                    fig['layout']['yaxis']['title'] = 'Piezas Esmaltadas'

                    p1.plotly_chart(fig, use_container_width=True)
                # -------------------------------------Plotly-----------------------------------------------------------
                # -------------------------------------Plotly-----------------------------------------------------------
                    iter_colum = esmalte_cons_grap.columns.values.tolist()[2:]
                    fig = go.Figure()
                    for elem in iter_colum:
                        fig.add_trace(go.Bar(
                            x=esmalte_cons_grap["Fecha_planta"],
                            y=np.round(esmalte_cons_grap[int(elem)],2),
                            #text=np.round(esmalte_cons_grap[int(elem)],2),textposition='auto',
                            name=elem))

                    # Here we modify the tickangle of the xaxis, resulting in rotated labels.
                    fig.update_layout(barmode='group', bargap=0.1,  bargroupgap=0.02, xaxis_tickangle=0)
                    fig.update_layout(height=500, width=700, legend=dict(orientation="v"))
                    fig.update_layout(template="seaborn", title="Esmalte consumido por referencia")

                    # Set x-axis and y-axis title
                    fig['layout']['xaxis']['title'] = 'Fecha'
                    fig['layout']['yaxis']['title'] = 'Esmaltade consumido en [Kg]'

                    p2.plotly_chart(fig, use_container_width=True)

                    # print(cantidad_piezas_grap["Fecha_planta"].unique())
                    # colum_name = cantidad_piezas_grap.columns.values.tolist()[2:]
                    #
                    # sum_cantidad_piezas_grap = pd.DataFrame(
                    #     '',
                    #     #index=range(int(cantidad_piezas_grap["Fecha_planta"].nunique())),
                    #     columns=["Fecha" , " Total"]
                    # )
                    # for i in cantidad_piezas_grap["Fecha_planta"].unique():
                    #     sum_cantidad_piezas_grap["Fecha"] = i
                    #     sum_cantidad_piezas_grap["Total"] = cantidad_piezas_grap[cantidad_piezas_grap["Fecha_planta"]
                    #                                                              == i][colum_name].sum().sum()
                    #     st.write(sum_cantidad_piezas_grap)


            # -------------------------------------Plotly-----------------------------------------------------------
            if st.checkbox("Reporte Manual"):
                t = pivot_ui(Analisis_df)
                with open(t.src) as t:
                    components.html(t.read(), width=1200, height=600, scrolling=True)


            st.subheader("5. Dispersión Esmaltado")
            # Reportes de las tablas dinamicas pre-establecidas
            if st.checkbox("Dispersión Esmaltado"):
                st.markdown("**Dispersión Esmaltado por Robot**")
                # Selección y filtrado de la base de datos
                ref = Analisis_df["Referencia"].unique()
                rob = Analisis_df["Robot"].unique()
                dt = Analisis_df["Fecha_planta"].unique()

                ss1, ss2 = st.columns((3,1))
                with ss2.form("Filtros"):
                    selec_ref1 =st.multiselect("¿Que referencia desea analizar?", ref, ref[:], key="ref1")
                    selec_robot1 =st.multiselect("¿Que robot desea analizar?", rob, rob[:], key="rob1")
                    selec_dt1 =st.multiselect("¿Que fecha desea analizar?", dt, dt[:], key="dt1")
                    st.form_submit_button("Filtrar")

                # Fitrado solo procesos completos
                report_df1 = Analisis_df[Analisis_df["Proceso_Completo"]== 1]
                report_df1 = report_df1[report_df1["Referencia"].isin(selec_ref1)]
                report_df1 = report_df1[report_df1["Robot"].isin(selec_robot1)]
                report_df1 = report_df1[report_df1["Fecha_planta"].isin(selec_dt1)]
                # -------------------------------------Plotly-----------------------------------------------------------
                fig = go.Figure()
                fig = px.box(report_df1, x="Robot", y="Esmalte_Usado [Kg]", color="Referencia",
                             points="outliers", #"all"
                             notched=False,template="seaborn")  # used notched shape

                fig.update_traces(marker=dict(size=2))
                fig.update_xaxes(type='category')
                fig.update_layout(height=700, width=700, legend=dict(orientation="v"))
                fig.update_layout(template="seaborn", title="Esmalte Usado por Referencia [Kg]")

                # Set x-axis and y-axis title
                fig['layout']['xaxis']['title'] = 'Robots'
                fig['layout']['yaxis']['title'] = 'Esmalte Usado'

                ss1.plotly_chart(fig, use_container_width=True)
                # -------------------------------------Plotly-----------------------------------------------------------
                st.markdown("**Dispersión Esmaltado en el Tiempo**")
                sss1, sss2 = st.columns((3,1))

                # Filtrado y selección
                sel_rob = sss2.selectbox("¿Que robot desea analizar?", rob, 0, key="rob0")
                data = Analisis_df[Analisis_df["Proceso_Completo"]== 1] # Solo procesos completos
                data = data[data["Robot"] == sel_rob]

                fig = px.box(data, x="Fecha_planta", y="Esmalte_Usado [Kg]", color="Referencia",template="seaborn",
                             orientation="v")

                fig.update_traces(marker=dict(size=2))
                fig.update_xaxes(type='category')
                fig.update_layout(height=700, width=700, legend=dict(orientation="v"))
                fig.update_layout(template="seaborn", title="Esmalte Usado por Referencia [Kg] en el "+ sel_rob)

                # Set x-axis and y-axis title
                fig['layout']['xaxis']['title'] = 'Fechas'
                fig['layout']['yaxis']['title'] = 'Esmalte Usado'

                sss1.plotly_chart(fig, use_container_width=True)
                # -------------------------------------Plotly-----------------------------------------------------------

if page == "Pre-Secadero":
    st.header('1. Pre-Secadero Madrid')
    st.subheader("Selección de Data a Analizar")
    st.markdown("**Opciones de Fecha**")
    sel_fecha = st.radio("¿Que periodo de tiempo desea analizar?",
                         ('Por día', 'Por rango de días'), key="fecha")
    if sel_fecha == "Por día":
        sel_dia = st.date_input("¿Que dia desea analizar?", datetime.date.today(), key="dia")
        if sel_dia > datetime.date.today():
            st.error("Recuerda que el día seleccionado no puede ser superior a la día actual")
            st.stop()
        st.info("Analizaras el día " + str(sel_dia))
    elif sel_fecha == "Por rango de días":
        sel_dia_ini = st.date_input("Seleccione el día inicial", datetime.date.today() -
                                    datetime.timedelta(days=1), key="dia_ini")
        sel_dia_fin = st.date_input("Seleccione el día final", datetime.date.today(), key="dia_fin")

        if sel_dia_fin <= sel_dia_ini:
            st.error("Recuerda seleccionar una fecha inicial anterior a la fecha final!!!")
            st.stop()
        elif sel_dia_fin > datetime.date.today():
            st.error("Recuerda que la fecha final no puede ser superior a la fecha actual")
            st.stop()
        else:
            st.info("Analizaras un periodo de tiempo de " + str((sel_dia_fin - sel_dia_ini).days +1 ) + " días." )

    if st.checkbox("Graficar Información", key="Presecadero"):
        with st.spinner('Descargando la información y dibujandola...'):
            if sel_fecha == "Por día":
                fig = sql_plot_presecadero(tipo="day", day=str(sel_dia), database='presecadero', table="presecadero")
                st.plotly_chart(fig, use_container_width=True)
            elif sel_fecha == "Por rango de días":
                fig = sql_plot_presecadero(tipo="rango", ini=str(sel_dia_ini), day=str(sel_dia_fin), database='presecadero',
                             table="presecadero")
                st.plotly_chart(fig, use_container_width=True)
