# Python File for streamlit tools
# Sales Baños y Cocna
# 03-August-2021
# ----------------------------------------------------------------------------------------------------------------------
# Libraries
import datetime
import time

import streamlit as st

# Internal Function
from SQL_Function import sql_plot, sql_plot_all, prev_day
import pyodbc
import pandas as pd
# ----------------------------------------------------------------------------------------------------------------------
# Streamlit Setting
st.set_page_config(page_title="IIOT - Corona",
                   initial_sidebar_state="collapsed",
                   page_icon="📈",
                   layout="wide")

tabs = ["Celula de Esmaltado", "Pre-Secadero"]
page = st.sidebar.radio("Tabs", tabs)
# ----------------------------------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------------------------------
# Initialize connection.
# Uses st.cache to only run once.
#@st.cache(persist=False, allow_output_mutation=True, suppress_st_warning=True, show_spinner=True, ttl=10)
@st.cache( ttl=10)
def sql_connect2(tipo="day", day="2021-04-28", ini="2021-04-27", hour=6, turno=1, server='EASAB101', database='robot1',
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

# Perform query.
#@st.cache(ttl=300)

tipo="day"
hour=6
turno=1
day="2021-09-14"
ini="2021-09-14"
database='robot1'
table="robot1"

while True:
    df = sql_connect2(tipo=tipo, day=day, ini=ini, hour=hour, turno=turno, database=database, table=table)
    st.write(df.shape)

    time.sleep(300)

#-----------------------------------------------------------------------------------------------------------------------
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

