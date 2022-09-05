# Python File function for streamlit tools
# SQL connection for IIOT | Colceramica
# 21-September-2021
# ----------------------------------------------------------------------------------------------------------------------
# Libraries
import datetime
import os

import numpy as np
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

from Plot_Function import plot_html, plot_html_all


# ----------------------------------------------------------------------------------------------------------------------
# Function definition
@st.experimental_memo(suppress_st_warning=True, show_spinner=True)
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

    # Drop the columns peso_antes y peso_despues if exist. These values will come from a different table
    df = df.drop(['peso_antes', 'peso_despues'], axis=1, errors="ignore")

    #TODO:  Poner la columna ID

    # Organizo las columnas del data frame
    re_columns = ['estado', 'fecha', 'referencia', 'sp_fmasico', 'fmasico', 'sp_patomizacion', 'patomizacion',
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


@st.experimental_memo(suppress_st_warning=True, show_spinner=True)
def get_data_day(sel_celula, sel_robot,  sel_dia, flag_download=False):
    """
    Programa que permite conectar con una base de dato del servidor y devuelve la base de dato como un pandas dataframe
    INPUT:
        Sel_celula = ['Célula 4', 'Célula 1']
        sel_robot = ["robot1", "robot2", "Ambos"]
        sel_dia = Día inicial EN STR
        redownload = Debe descargarse la data o buscar dentro de los archivos previamente descargados
    OUTPUT:
        df = pandas dataframe traido de la base de dato SQL, puede ser robot 1 o robot 2
        df2 = pandas dataframe traido de la base de dato SQL, siempre es robot 2
        salud_list = lista con el dato de salud por día
        salud_datos = Numero | Salud total de los datos
        title = Titulo para la grafica
    """
    # Definición del rango de fecha seleccionado
    segundos_dias = 86400

    # Por Robot
    if sel_celula == 'Célula 4':
        # Adjust in the reference name
        dict_replace = {37: 9147, 38: 9311, 39: 9312}
        # Por día
        if sel_robot == "Ambos":
            # Conexión y manejo robot 1
            df = find_load(tipo="day_planta", day=str(sel_dia), ini=None, database="robot1",
                           table="robot1", redownload=flag_download)
            df = fecha_format(df)
            df["robot"] = "robot1"

            # Conexión y manejo robot 2
            df2 = find_load(tipo="day_planta", day=str(sel_dia), ini=None, database="robot2",
                            table="robot2", redownload=flag_download)
            df2 = fecha_format(df2)
            df2["robot"] = "robot2"

            # Defining the title and filename for saving the plots
            title = "Variables Robots de Esmaltado Día " + str(sel_dia)

            # Rename the following references in columns
            df["referencia"].replace(dict_replace, inplace=True)
            df2["referencia"].replace(dict_replace, inplace=True)

        else:
            # Definición del robot seleccionado
            tabla_sql = sel_robot.lower().replace(" ", "")
            # Empty second DF
            df2 = None

            # Conexión y manejo robot 1
            df = find_load(tipo="day_planta", day=str(sel_dia), ini=None, database=tabla_sql,
                           table=tabla_sql, redownload=flag_download)
            df = fecha_format(df)
            df["robot"] = tabla_sql

            # Defining the title and filename for saving the plots
            title = "Variables " + tabla_sql + " de Esmaltado Día " + str(sel_dia)

            # Rename the following references in columns
            df["referencia"].replace(dict_replace, inplace=True)

    elif sel_celula == 'Célula 1':
        # Empty second DF
        df2 = None

        # Conexión y manejo celula 1
        df = find_load(tipo="day_planta", day=str(sel_dia), ini=None, database='Celula1GR',
                       table='Celula1GR', redownload=flag_download)
        df = fecha_format(df)

        df["robot"] = 'robot1'

        # Defining the title and filename for saving the plots
        title = "Variables Celula 1 de Esmaltado Día " + str(sel_dia)

    # Salud de los datos
    salud_datos = (df.shape[0] / segundos_dias) * 100
    salud_list = [np.round(salud_datos, 2)]

    return df, df2, salud_list, salud_datos, title


@st.experimental_memo(suppress_st_warning=True, show_spinner=True)
def get_data_range(sel_celula, sel_robot, sel_dia_ini, sel_dia_fin, flag_download=False):
    """
    Programa que permite conectar con una base de dato del servidor y devuelve la base de dato como un pandas dataframe
    del periodo de fecha ingresado
    INPUT:
        sel_celula = ['Célula 4', 'Célula 1']
        sel_robot = ["robot1", "robot2", "Ambos"]
        sel_dia_ini = Día inicial en STR ("2022-01-01")
        sel_dia_fin = Día final en STR ("2022-01-02")
        redownload = Debe descargarse la data o buscar dentro de los archivos previamente descargados
    OUTPUT:
        df = pandas dataframe traído de la base de dato SQL, puede ser robot 1 o robot 2
        df2 = pandas dataframe traído de la base de dato SQL, siempre es robot 2
        salud_list = lista con el dato de salud por día
        salud_datos = Numero | Salud total de los datos
        title = Titulo para la gráfica
        """
    # Definición del rango de fecha seleccionado
    segundos_dias = 86400

    # Por Robot
    if sel_celula == 'Célula 4':
        # Saving the salud datos of the period
        title_salud = "Salud_Cel4_" + str(sel_dia_ini) + "_y_" + str(sel_dia_fin)

        # Por rango
        if sel_robot == "Ambos":
            # Conexión y manejo robot 1
            df = find_load(tipo="rango_planta", ini=str(sel_dia_ini), day=str(sel_dia_fin), database="robot1",
                           table="robot1", redownload=flag_download)
            df = fecha_format(df)
            df["robot"] = "robot1"

            # Conexión y manejo robot 2
            df2 = find_load(tipo="rango_planta", ini=str(sel_dia_ini), day=str(sel_dia_fin), database="robot2",
                            table="robot2", redownload=flag_download)
            df2 = fecha_format(df2)
            df2["robot"] = "robot2"

            # Defining the title and filename for saving the plots
            title = "Variables Robots de Esmaltado entre " + str(sel_dia_ini) + " y " + str(sel_dia_fin)
        else:
            # Definición del robot seleccionado
            tabla_sql = sel_robot.lower().replace(" ", "")
            # Empty second DF
            df2 = None

            # Conexión y manejo robot 1 o robot 2
            df = find_load(tipo="rango_planta", ini=str(sel_dia_ini), day=str(sel_dia_fin), database='Celula1GR',
                           table='Celula1GR', redownload=flag_download)
            df = fecha_format(df)
            df["robot"] = 'robot1'

            # Defining the title and filename for saving the plots
            title = "Variables_Celula_1 de Esmaltado entre " + str(sel_dia_ini) + " y " + str(sel_dia_fin)

    elif sel_celula == 'Célula 1':
        # Saving the salud datos of the period
        title_salud = "Salud_Cel1_" + str(sel_dia_ini) + "_y_" + str(sel_dia_fin)

        # Conexión y manejo Celula 1
        df = find_load(tipo="rango_planta", ini=str(sel_dia_ini), day=str(sel_dia_fin), database='Celula1GR',
                       table='Celula1GR', redownload=flag_download)
        df = fecha_format(df)
        df["robot"] = 'Cel_1_R1'

        # Defining the title and filename for saving the plots
        title = "Variables Celula 1 de Esmaltado entre " + str(sel_dia_ini) + " y " + str(sel_dia_fin)

        # Empty second DF
        df2 = None

    # Salud de cada día en el periodo
    salud_list = []
    sel_dia_ini_aux = sel_dia_ini
    while sel_dia_ini_aux <= sel_dia_fin:
        df_filter = df.loc[(df.index >= str(sel_dia_ini_aux) + ' 06:00:00') &
                           (df.index <= str(sel_dia_ini_aux + datetime.timedelta(days=1)) + ' 05:59:59')]

        salud_dia = np.round((df_filter.shape[0] / segundos_dias) * 100, 2)
        salud_list.append(salud_dia)
        # Avanzo un día
        sel_dia_ini_aux = sel_dia_ini_aux + datetime.timedelta(days=1)
    salud_datos = sum(salud_list) / len(salud_list)


    with open('./Data/Analizadas/' + title_salud + '.txt', 'w') as f:
        f.write('%.2f' % salud_datos)

    return df, df2, salud_list, salud_datos, title


# No poner cache en esta función para poder cargar los ultimos datos del día.
def find_load(tipo, day, ini, database, table, redownload):
    """
    Función que busca y carga el archivo de datos si este ya ha sido descargado. En caso contrario lo descarga a través
    de la función sql_connet
    INPUT:
        tipo: ["day_planta", "rango_planta"]
        day: día final o unico día a analizar como STR ("2022-01-01")
        ini: día inicial a analizar en el rango como STR ("2021-12-28")
        database: base de dato a la cual se debe conectar
        table: tabla a la cual se debe conectar
        redownload = TRUE or FALSE statement si es TRUE se omite la parte de buscar el archivo y se descarga nuevamente.
    OUTPUT:
        pd_sql: dataframe con los datos buscados o descargados
    """
    # Setting the folder where to search
    directory = './Data/Raw/' + day[:-3] + '/'
    if not os.path.exists(directory):
        os.makedirs(directory)
    filenames = os.listdir(directory)

    # Empty dataframe
    pd_sql = pd.DataFrame()

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

        # Recorro los días de ese periodo de tiempo
        while ini_date <= day_date:
            # Setting the folder where to search
            directory = './Data/Raw/' + str(ini_date)[:-3] + '/'
            if not os.path.exists(directory):
                os.makedirs(directory)
            filenames = os.listdir(directory)

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


# No poner cache en esta función para poder cargar los ultimos datos del día
def sql_connect(tipo, day, database, table):  # hour=6
    """
    Programa que permite conectar con una base de dato del servidor y devuelve la base de dato como un pandas dataframe
    INPUT:
        tipo = ["day_planta", "day"]
        day = Día a descargar en  STR ("2021-04-28")
        database: base de dato a la cual se debe conectar
        table: tabla a la cual se debe conectar
    OUTPUT:
        pd_sql = pandas dataframe traído de la base de dato SQL
    """
    # Connection keys
    load_dotenv('./.env')

    server = os.environ.get("SERVER")
    username = os.environ.get("USER_SQL")
    password = os.environ.get("PASSWORD")

    # Connecting to the sql database
    connection_str = "DRIVER={SQL Server};SERVER=%s;DATABASE=%s;UID=%s;PWD=%s" % (server, database, username, password)
    connection_url = URL.create("mssql+pyodbc", query={"odbc_connect": connection_str})

    conn = create_engine(connection_url)
    # ------------------------------------------------------------------------------------------------------------------
    # Tipos de conexiones establecidas para traer distintas cantidades de datos
    # ------------------------------------------------------------------------------------------------------------------
    if tipo == "day":
        pd_sql = pd.read_sql_query("SELECT * FROM " + database + ".dbo." + table + " WHERE fecha like '" + day + "'",
                                   conn)

        # Guardando los datos en archivos estaticos
        if day == str(datetime.date.today()):
            pass  # No guardar datos si el día seleccionado es el día actual del sistema
        else:
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
        if day == str(datetime.date.today()):
            pass  # No guardar datos si el día seleccionado es el día actual del sistema
        else:
            # Checking and creating the folder
            folder = day[:-3]
            if not os.path.exists('./Data/Raw/' + folder):
                os.makedirs('./Data/Raw/' + folder)
            # Saving the raw data
            pd_sql.to_csv('./Data/Raw/' + folder + '/tabla_' + table + '_' + day + '.csv', index=False)

    return pd_sql


def sql_plot_live(sel_celula, time, day):
    """
    Función que se conecta a la base de dato y crea el archivo de visualización a la vez que lo guarda
    INPUT:
        sel_celula = Célula a la que nos conectaremos (base de datos)
        time = tiempo a visualizar
        day = Día inicial EN STR ("2021-04-28")
    OUTPUT:
        df = pandas dataframe traido de la base de dato 1 del SQL
        df2 = pandas dataframe traido de la base de datos 2 del SQL
        fig = objeto figura para dibujarlo externamente de la función
    """
    if sel_celula == 'Célula 4':
        # Conexión y manejo robot 1
        df = sql_connect_live(time=time, day=day, database="robot1", table="robot1")
        df = fecha_format(df)
        df["robot"] = "robot1"

        # Conexión y manejo robot 2
        df2 = sql_connect_live(time=time + 20, day=day, database="robot2", table="robot2")
        df2 = fecha_format(df2)
        df2["robot"] = "robot2"

        df2 = df2.loc[df.index[0]:df.index[-1], :]

        # Defining the title and filename for saving the plots
        title = "Variables Robots de Esmaltado Día " + day + ' ' + sel_celula

        # Plotting the DF
        fig = plot_html_all(df, df2, title)

    elif sel_celula == 'Célula 1':
        # Conexión y manejo robot 1
        df = sql_connect_live(time=time, day=day, database="Celula1GR", table="Celula1GR")
        df = fecha_format(df)
        df["robot"] = "robot1"

        # Empty dataframe
        df2 = None

        # Defining the title and filename for saving the plots
        title = "Variables Robots de Esmaltado Día " + day + ' ' + sel_celula

        # Plotting the DF
        fig = plot_html(df, title)

    return df, df2, fig


def sql_connect_live(time, day, database, table):  # hour=6
    """
    Programa que permite conectar con una base de dato del servidor descargar los ultimos registros denotados en time
    INPUT:
        time = int | Cantidad de ultimos registros a descargar
        day = Día de los registros que se deben descargar en  STR ("2021-04-28")
        database: base de dato a la cual se debe conectar
        table: tabla a la cual se debe conectar
    OUTPUT:
        pd_sql = pandas dataframe traido de la base de dato SQL
    """

    # Connection keys
    load_dotenv('./.env')

    server = os.environ.get("SERVER")
    username = os.environ.get("USER_SQL")
    password = os.environ.get("PASSWORD")

    # Connecting to the sql database
    connection_str = "DRIVER={SQL Server};SERVER=%s;DATABASE=%s;UID=%s;PWD=%s" % (server, database, username, password)
    connection_url = URL.create("mssql+pyodbc", query={"odbc_connect": connection_str})

    conn = create_engine(connection_url)
    # ------------------------------------------------------------------------------------------------------------------
    # Tipos de conexiones establecidas para traer distintas cantidades de datos
    # ------------------------------------------------------------------------------------------------------------------

    pd_sql = pd.read_sql_query('SELECT TOP ' + str(time) + ' * FROM ' + database + '.dbo.' + table +
                               " WHERE fecha like '" + day + "'" + ' ORDER BY hora DESC, minuto DESC, '
                                                                   'segundo DESC ', conn)

    return pd_sql
