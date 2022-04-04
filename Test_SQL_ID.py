# Python File function for streamlit tools
# SQL connection for IIOT | Colceramica
# 04-April-2022
# ----------------------------------------------------------------------------------------------------------------------
# Libraries
import datetime
import os

import pandas as pd
import pyodbc


# ----------------------------------------------------------------------------------------------------------------------
# Function definition
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

    # Ordeno la data por la fecha
    df = df.sort_values(by='fecha', ascending=True)

    df.set_index("fecha", inplace=True)

    return df


# ----------------------------------------------------------------------------------------------------------------------
tipo = "day_planta"
day = "2022-04-02"

server = 'EASAB101'
database = 'celula4'
table = "celula4"

username = 'IOTVARPROC'
password = '10Tv4rPr0C2021*'
# ----------------------------------------------------------------------------------------------------------------------
# Connecting to the sql database
conn = pyodbc.connect(
    'driver={SQL Server};server=%s;database=%s;uid=%s;pwd=%s' % (server, database, username, password))

if tipo == "day_planta":
    ini, fin = add_day(day)
    pd_sql_1 = pd.read_sql_query("SELECT * FROM " + database + ".dbo." + table + " WHERE fecha like '" + ini + "'"
                                 + " AND hora between 6 and 23", conn)

    pd_sql_2 = pd.read_sql_query("SELECT * FROM " + database + ".dbo." + table + " WHERE fecha like '" + fin + "'"
                                 + " AND hora between 0 and 5", conn)
    pd_sql = pd.concat([pd_sql_1, pd_sql_2])

# Checking and creating the folder
FOLDER = day[:-3]
if not os.path.exists('./Data/Pesos/' + FOLDER):
    os.makedirs('./Data/Pesos/' + FOLDER)
# Saving the raw data
pd_sql.to_csv('./Data/Pesos/' + FOLDER + '/tabla_' + table + '_' + day + '.csv', index=False)

# Formatting the DF
df = fecha_format(pd_sql)

# Saving the raw data
df.to_excel('./Data/Pesos/' + FOLDER + '/Pesos_' + table + '_' + day + '.xlsx', index=True)

print(df.head(20))
