# Python File function for streamlit tools
# Sales Baños y Cocna
# 03-August-2021
# ----------------------------------------------------------------------------------------------------------------------
# Libraries
import pandas as pd

import datetime
import calendar as cl

import streamlit as st
import pyodbc

from Plot_Function import plot_html, plot_html_all, plot_html_presecadero
# ----------------------------------------------------------------------------------------------------------------------

# Function definition
@st.cache(persist=False, allow_output_mutation=True, suppress_st_warning=True, show_spinner=False)
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