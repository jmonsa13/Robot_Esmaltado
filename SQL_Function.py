# Python File function for streamlit tools
# SQL connection for IIOT | Colceramica
# 21-September-2021
# ----------------------------------------------------------------------------------------------------------------------
# Libraries
import os
import calendar as cl
import datetime

import pandas as pd
import pyodbc
import streamlit as st

from Plot_Function import plot_html, plot_html_all
# ----------------------------------------------------------------------------------------------------------------------
# Function definition


@st.cache(persist=False, allow_output_mutation=True, suppress_st_warning=True, show_spinner=False)
def load_data(folder="./Data/Raw/", filename="tabla_robot1_2021_04_22_1012.csv"):
    """
    Función que carga el archivo csv guardado al conectar con la base de datos y devuelve un dataframe
    """
    df = pd.read_csv(folder + filename)

    return df


def fecha_format(df):
    """
    Función que hace el manejo de la columna de fecha de la base de datos
    """
    # Organizar el tema de fecha
    df["fecha"] = pd.to_datetime(df['fecha'], format='%Y/%m/%d', exact=False)
    df["fecha"] = df["fecha"].dt.normalize()
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

    # Organizo las columnas del data frame
    re_columns = ['estado', 'fecha', 'referencia', 'peso_antes', 'peso_despues', 'sp_fmasico', 'fmasico',
                  'sp_patomizacion', 'patomizacion',
                  'sp_pabanico', 'pabanico', 'presion_red', 'año', 'mes', 'dia', 'ndia', 'hora', 'minuto', 'segundo',
                  "fecha_planta"]
    df = df[re_columns]

    # Ordeno la data por la fecha
    df = df.sort_values(by='fecha', ascending=True)

    df.set_index("fecha", inplace=True)

    return df


def add_day(day, add=1):
    """
    Función agrega o quita dias, teniendo en cuenta inicio de mes e inicio de año
    INPUT
        day = "2021-02-01"  EN STRING
    OUTPUT
        ini_date = día entregado en STR
        fin_date = día con los días sumados o restados en STR al día ingresado
    """
    l_day_n = [int(x) for x in day.split("-")]
    ini_date = datetime.date(l_day_n[0], l_day_n[1], l_day_n[2])
    fin_date = ini_date + datetime.timedelta(days=add)

    return str(ini_date), str(fin_date)


#@st.cache(persist=False, allow_output_mutation=True, suppress_st_warning=True, show_spinner=True)
def find_load(tipo, day, ini, database, table, redownload):
    """
    Función que busca y carga el archivo de datos si este ya ha sido descargado.
    INPUT:
        tipo:
    OUTPUT:
        pd_sql: dataframe con los datos
    """
    directory = './Data/Raw/'
    filenames = os.listdir(directory)

    if tipo == "day_planta":
        # Creo el nombre del archivo a buscar
        filename = 'tabla_' + table + '_' + day + '.csv'
        if filename in filenames and redownload is False:
            pd_sql = load_data(folder=directory, filename=filename)
        else:
            pd_sql = sql_connect(tipo=tipo, day=day, database=database, table=table)

    elif tipo == "rango_planta":
        # Fecha Inicial
        l_ini_n = [int(x) for x in ini.split("-")]
        ini_date = datetime.date(l_ini_n[0], l_ini_n[1], l_ini_n[2])
        # Fecha Final
        l_day_n = [int(x) for x in day.split("-")]
        day_date = datetime.date(l_day_n[0], l_day_n[1], l_day_n[2])
        # Empty datafram
        pd_sql = pd.DataFrame()

        # Recorro los días de ese periodo de tiempo
        while ini_date <= day_date:
            # Creo el nombre del archivo a buscar
            filename = 'tabla_' + table + '_' + str(ini_date) + '.csv'
            if filename in filenames and redownload is False:
                aux = load_data(folder=directory, filename=filename)
            else:
                aux = sql_connect(tipo="day_planta", day=str(ini_date), database=database, table=table)

            pd_sql = pd.concat([pd_sql, aux])
            # Avanzo un día
            ini_date = ini_date + datetime.timedelta(days=1)

    return pd_sql


@st.cache(persist=False, allow_output_mutation=True, suppress_st_warning=True, show_spinner=True)
def sql_connect(tipo="day", day="2021-04-28", server='EASAB101', database='robot1',
                table="robot1", username='IOTVARPROC', password='10Tv4rPr0C2021*'):  # hour=6
    """
    Programa que permite conectar con una base de dato del servidor y devuelve la base de dato como un pandas dataframe
    INPUT:
        tipo = ["day", "all", "turno", "rango"]
        day = Día inicial EN STR
    OUTPUT:
        pd_sql = pandas dataframe traido de la base de dato SQL
    """
    # Connecting to the sql database
    conn = pyodbc.connect(
        'driver={SQL Server};server=%s;database=%s;uid=%s;pwd=%s' % (server, database, username, password))
    # ------------------------------------------------------------------------------------------------------------------
    # Tipos de conexiones establecidas para traer distintas cantidades de datos
    # ------------------------------------------------------------------------------------------------------------------
    if tipo == "day":
        pd_sql = pd.read_sql_query("SELECT * FROM " + database + ".dbo." + table + " WHERE fecha like '" + day + "'",
                                   conn)

        # Guardando los datos en archivos estaticos
        pd_sql.to_csv('./Data/Raw/tabla_' + table + '_' + day + '.csv', index=False)
        # pd_sql.to_excel('./Data/Raw/tabla_' + table + '_'+ day + '.xlsx', index = False )

    elif tipo == "day_planta":
        ini, fin = add_day(day)
        pd_sql_1 = pd.read_sql_query("SELECT * FROM " + database + ".dbo." + table + " WHERE fecha like '" + ini + "'"
                                     + " AND hora between 6 and 23", conn)

        pd_sql_2 = pd.read_sql_query("SELECT * FROM " + database + ".dbo." + table + " WHERE fecha like '" + fin + "'"
                                     + " AND hora between 0 and 5", conn)
        pd_sql = pd.concat([pd_sql_1, pd_sql_2])
        # Guardando los datos en archivos estaticos
        pd_sql.to_csv('./Data/Raw/tabla_' + table + '_' + day + '.csv', index=False)

    return pd_sql


@st.cache(persist=False, allow_output_mutation=True, suppress_st_warning=True, show_spinner=True)
def sql_plot(tipo="day", turno=1, day="2021-04-28", ini="2021-04-27", database='robot1', table="robot1",
             redownload=False):
    """
    Función que se conecta a la base de dato y crea el archivo de visualización a la vez que lo guarda
    INPUT:
        tipo = ["day", "all", "turno", "rango"]
        turno = 1 or 2 or 3
        day = Día inicial EN STR
        ini = Día final EN STR (util cuando el tipo es rango)
        database = Base de dato a la cual conectarse
        table = tabla a la base de dato a la cual conectarse
    OUTPUT:
        df = pandas dataframe traido de la base de dato SQL
        fig = objeto figura para dibujarlo externamente de la función
    """
    # Iniciación variables
    title = ""

    # Conexión y manejo robot 1
    df = find_load(tipo=tipo, day=day, ini=ini, database=database, table=table, redownload=redownload)
    df = fecha_format(df)
    df["robot"] = table

    # Defining the title and filename for saving the plots
    if tipo == "day" or tipo == "day_planta":
        title = "Variables " + table + " de Esmaltado Día " + day
    elif tipo == "rango" or tipo == "rango_planta":
        title = "Variables " + table + " de Esmaltado entre " + ini + " y " + day

    # Plotting the DF
    fig = plot_html(df, title)
    return df, fig


@st.cache(persist=False, allow_output_mutation=True, suppress_st_warning=True, show_spinner=True)
def sql_plot_all(tipo="day", day="2021-04-28", ini="2021-04-27", redownload=False):
    """
    Función que se conecta a la base de datos de ambos robots y crea el archivo de visualización a la vez que lo guarda
    INPUT:
        tipo = ["day", "all", "turno", "rango"]
        turno = 1 or 2 or 3
        day = Día inicial EN STR
        ini = Día final EN STR (util cuando el tipo es rango)
    OUTPUT:
        df = pandas dataframe traido de la base de dato SQL del robot 1
        df2 = pandas dataframe traido de la base de dato SQL del robot 2
        fig = objeto figura para dibujarlo externamente de la función
    """
    # Iniciación variables
    title = ""
    # Conexión y manejo robot 1
    df = find_load(tipo=tipo, day=day, ini=ini, database="robot1", table="robot1", redownload=redownload)
    df = fecha_format(df)
    df["robot"] = "robot1"

    # Conexión y manejo robot 2
    df2 = find_load(tipo=tipo, day=day, ini=ini, database="robot2", table="robot2", redownload=redownload)
    df2 = fecha_format(df2)
    df2["robot"] = "robot2"

    # Defining the title and filename for saving the plots
    if tipo == "day" or tipo == "day_planta":
        title = "Variables Robots de Esmaltado Día " + day
    elif tipo == "rango" or tipo == "rango_planta":
        title = "Variables Robots de Esmaltado entre " + ini + " y " + day

    # Plotting the DF
    fig = plot_html_all(df, df2, title)

    return df, df2, fig
