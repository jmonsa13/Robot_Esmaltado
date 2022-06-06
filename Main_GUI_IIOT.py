# Python File for streamlit tools
# GUI APP for IIOT | Corona
# 21-September-2021
# ----------------------------------------------------------------------------------------------------------------------
# Libraries
import datetime
import os
import time

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from pivottablejs import pivot_ui

# Internal Function
from Analysis_Function import find_analisis, visual_tabla_dinam, sum_procesos
from Plot_Function import plot_bar_referencia, plot_bar_turno, plot_total, plot_html_all, plot_html,\
    plot_tiempo_muerto, plot_bar_acum_tiempo_muerto
from SQL_Function import sql_plot_live, sql_connect_live, fecha_format, get_data_day, get_data_range, load_data

# ----------------------------------------------------------------------------------------------------------------------
# Streamlit Setting
st.set_page_config(page_title="Celula de Esmaltado - Corona",
                   initial_sidebar_state="collapsed",
                   page_icon="📈",
                   layout="wide")

tabs = ["Resumen Mensual", "Día a Día", "Online"]
page = st.sidebar.radio("Paginas", tabs, index=1)
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# Initial page
st.title(' 📈 Celula de Esmaltado - Corona 🤖')

# Global variables
error_list = [0, 54, 58, 62, 101, 118, 126, 127]  # ME QUEDO SOLO CON LAS REFERENCIAS REALES DEL PROCESO
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
if page == "Resumen Mensual":
    st.header('Resumen Mensual Celula Robotizada Girardota')
    # Folder path definition
    directory = './Data/Analisis_Mensual/'
    folders = os.listdir(directory)

    # Empty data frame and list
    analisis_meses = pd.DataFrame()
    salud_mes = []

    # Loading the DF of each month in a unique DF
    for folder in folders:
        files = os.listdir(directory + folder)
        for file in files:
            if file.split("_", 1)[0] == "Salud":
                with open(directory + folder + '/' + file, "r", encoding="utf-8") as salud_file:
                    salud_mes.append(float(salud_file.readline()))

            else:
                analisis_meses = pd.concat([analisis_meses, load_data(folder=directory + folder + '/', filename=file)])

    # Re.setting index
    analisis_meses.reset_index(drop=True, inplace=True)

    # Eliminando los días en la columna de fecha planta
    analisis_meses["Fecha_AñoMes_planta"] = analisis_meses["Fecha_planta"].apply(lambda x: x[:-3])
    analisis_meses["Fecha_Dia_planta"] = analisis_meses["Fecha_planta"].apply(lambda x: x[-2:])
    # ----------------------------------------------------------------------------------------------------------
    # FILTROS para los analisis y reportes
    # ----------------------------------------------------------------------------------------------------------
    # Solo reporto los procesos que tuvieron algún consumo de esmalte.
    analisis_meses = analisis_meses[analisis_meses["Esmalte_Usado [Kg]"] != 0]

    # Solo reporto los procesos que finalizaron el día que estoy contando.
    analisis_meses = analisis_meses[(analisis_meses["Proceso_Completo"] == 1) |
                                    (analisis_meses["Proceso_Completo"] == -1)]

    # No cuento los procesos que son códigos de error
    analisis_meses = analisis_meses[~(analisis_meses["Referencia"].isin(error_list))]
    # ------------------------------------------------------------------------------------------------------
    # TABLAS DINAMICAS
    # ------------------------------------------------------------------------------------------------------
    # Tablas dinamicas de cantidad de piezas
    cantidad_piezas = analisis_meses.pivot_table(index=["Fecha_AñoMes_planta", "Robot", "Turno"],
                                                 values="Proceso_Completo",
                                                 columns="Referencia", aggfunc=len,
                                                 fill_value=0, margins=False)

    cantidad_piezas_grap = analisis_meses.pivot_table(index=["Fecha_AñoMes_planta", "Robot"],
                                                      values="Proceso_Completo",
                                                      columns="Referencia", aggfunc=len,
                                                      fill_value=0, margins=False).reset_index()

    cantidad_piezas = cantidad_piezas.reset_index()
    cantidad_piezas.columns = list(map(str, cantidad_piezas.columns.values.tolist()))
    cantidad_piezas_grap.columns = list(map(str, cantidad_piezas_grap.columns.values.tolist()))
    # ------------------------------------------------------------------------------------------------------
    # Tablas dinamicas de esmalte consumido por pieza
    esmalte_cons = analisis_meses.pivot_table(index=["Fecha_AñoMes_planta", "Robot", "Turno"],
                                              values="Esmalte_Usado [Kg]",
                                              columns="Referencia", aggfunc='sum',
                                              fill_value=0, margins=False)

    esmalte_cons_grap = analisis_meses.pivot_table(index=["Fecha_AñoMes_planta", "Robot"],
                                                   values="Esmalte_Usado [Kg]",
                                                   columns="Referencia", aggfunc='sum', fill_value=0,
                                                   margins=False).reset_index()

    esmalte_cons = esmalte_cons.reset_index()
    esmalte_cons.columns = list(map(str, esmalte_cons.columns.values.tolist()))
    esmalte_cons_grap.columns = list(map(str, esmalte_cons_grap.columns.values.tolist()))
    # ----------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------
    # Reporte grafico Total
    # ----------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------
    st.markdown("**Graficas de Piezas Fabricadas y Esmalte Consumido Total por Mes**")
    st.markdown("Solo las referencias de productos")

    # Gráfica de total de piezas fabricadas por mes
    sum_cant_mensual = sum_procesos(cantidad_piezas_grap, "Piezas Esmaltadas_Mensual", column="Fecha_AñoMes_planta")

    c1, c2 = st.columns(2)
    # -------------------------------------Plotly---------------------------------------------------------------
    fig = plot_total(sum_cant_mensual, salud_mes, "Piezas Esmaltadas Mensualmente por Robot", "Piezas Esmaltadas [Und]",
                     fecha_column="Fecha_AñoMes_planta", flag=False)
    fig.update_xaxes(dtick="M1", tickformat="%b\n%Y")
    fig.update_layout(xaxis_tickangle=0, barmode='group')

    c1.plotly_chart(fig, use_container_width=True)
    # ----------------------------------------------------------------------------------------------------------
    # Sumo el esmalte total en ambos o solo 1 robot
    sum_esmalte = sum_procesos(esmalte_cons_grap, "Esmalte Usado", column="Fecha_AñoMes_planta")

    x_column = sum_esmalte.columns.values.tolist()[1:]
    sum_esmalte["Total"] = 0
    for i in x_column:
        if i != "Total":
            sum_esmalte["Total"] += sum_esmalte[i]

    # PLOTLY
    fig = plot_total(sum_esmalte, salud_mes, "Esmalte Usado por Robot y Total", "Esmalte Usado [Kg]",
                     fecha_column="Fecha_AñoMes_planta", flag=False)
    fig.update_xaxes(dtick="M1", tickformat="%b\n%Y")
    fig.update_layout(xaxis_tickangle=0)

    c2.plotly_chart(fig, use_container_width=True)
    # ----------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------
    # Reporte grafico por turno
    # ----------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------
    # Filtrado y selección
    st.markdown("**Graficas de Piezas Fabricadas y Esmalte Consumido por Turno cada Mes**")
    sel_rob1 = st.selectbox("¿Que robot desea analizar?", list(cantidad_piezas["Robot"].unique()),
                            0, key="rob_Gen")
    # ----------------------------------------------------------------------------------------------------------
    # Cantidad de Piezas Esmaltadas
    g1, g2 = st.columns(2)
    # Filtro el DF por la selección realizada
    cantidad_piezas_filter_gen = cantidad_piezas[cantidad_piezas["Robot"] == sel_rob1]

    # Organizo la data para poderla dibujar
    df_turno = pd.melt(frame=cantidad_piezas_filter_gen, id_vars=["Fecha_AñoMes_planta", "Robot", "Turno"],
                       var_name="Referencia", value_name="Cantidad")

    df_turno = df_turno.groupby(["Fecha_AñoMes_planta", "Robot", "Turno"]).sum().reset_index()
    # -------------------------------------Plotly---------------------------------------------------------------
    # Cantidad de piezas esmaltadas
    fig = plot_bar_turno(df=df_turno, salud=salud_mes,
                         title="Cantidad Piezas Esmaltadas por Mes y Turno {}".format(sel_rob1.title()),
                         ytitle='Piezas Esmaltadas [Und]',
                         fecha_column="Fecha_AñoMes_planta")
    fig.update_xaxes(dtick="M1", tickformat="%b\n%Y")
    fig.update_layout(xaxis_tickangle=0)

    g1.plotly_chart(fig, use_container_width=True)
    # ----------------------------------------------------------------------------------------------------------
    # Cantidad de Esmalte usado
    # Filtro el DF por la selección realizada
    esmalte_cons_filt2 = esmalte_cons[esmalte_cons["Robot"] == sel_rob1]

    # Organizo la data para poderla dibujar
    df_turno = pd.melt(frame=esmalte_cons_filt2, id_vars=["Fecha_AñoMes_planta", "Robot", "Turno"],
                       var_name="Referencia", value_name="Cantidad")

    df_turno = df_turno.groupby(["Fecha_AñoMes_planta", "Robot", "Turno"]).sum().reset_index()
    # -------------------------------------Plotly---------------------------------------------------------------
    # Cantidad de Esmalte esmaltadas
    fig = plot_bar_turno(df=df_turno, salud=salud_mes,
                         title="Cantidad Esmalte Consumido por Día y Turno {}".format(sel_rob1.title()),
                         ytitle='Esmalte Consumido [Kg]',
                         fecha_column="Fecha_AñoMes_planta")
    fig.update_xaxes(dtick="M1", tickformat="%b\n%Y")
    fig.update_layout(xaxis_tickangle=0)
    g2.plotly_chart(fig, use_container_width=True)
    # ----------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------
    # Reporte grafico por referencia
    # ----------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------
    # Graficas de los reportes generados
    st.markdown("**Graficas de Piezas Fabricadas y Esmalte Consumido por Robot, Referencia cada Mes**")
    gg1, gg2 = st.columns(2)

    # Filtrado y selección
    sel_rob0 = gg1.selectbox("¿Que robot desea analizar?", list(cantidad_piezas["Robot"].unique()), 0, key="rob00")

    sel_turno = gg2.selectbox("¿Que turno desea analizar?", ["Día Completo"] +
                              list(cantidad_piezas["Turno"].unique()), 0, key="Turno")

    # Filtrado por el turno y el robot
    if sel_turno == "Día Completo":
        # Sin información de turnos
        cantidad_piezas_filt = cantidad_piezas_grap[cantidad_piezas_grap["Robot"] == sel_rob0]
        esmalte_cons_filt = esmalte_cons_grap[esmalte_cons_grap["Robot"] == sel_rob0]

    else:
        # Con información de turno
        cantidad_piezas_turno = cantidad_piezas[cantidad_piezas["Turno"] == sel_turno]
        esmalte_cons_turno = esmalte_cons[esmalte_cons["Turno"] == sel_turno]

        cantidad_piezas_turno.drop("Turno", inplace=True, axis=1)
        esmalte_cons_turno.drop("Turno", inplace=True, axis=1)

        cantidad_piezas_filt = cantidad_piezas_turno[cantidad_piezas_turno["Robot"] == sel_rob0]
        esmalte_cons_filt = esmalte_cons_turno[esmalte_cons_turno["Robot"] == sel_rob0]

    # -------------------------------------Plotly---------------------------------------------------------------
    # Cantidad de piezas esmaltadas
    fig = plot_bar_referencia(df=cantidad_piezas_filt, salud=salud_mes,
                              title="Cantidad de Piezas Esmaltadas {} y Turno {}".format(sel_rob0.title(),
                                                                                         sel_turno),
                              ytitle='Piezas Esmaltadas [Und]',
                              fecha_column="Fecha_AñoMes_planta")
    fig.update_xaxes(dtick="M1", tickformat="%b\n%Y")
    fig.update_layout(xaxis_tickangle=0)

    gg1.plotly_chart(fig, use_container_width=True)

    # -------------------------------------Plotly---------------------------------------------------------------
    # Cantidad de esmalte usado
    fig = plot_bar_referencia(df=esmalte_cons_filt, salud=salud_mes,
                              title="Esmalte Consumido por Referencia {} y Turno {}".format(sel_rob0.title(),
                                                                                            sel_turno),
                              ytitle='Esmalte Consumido [Kg]',
                              fecha_column="Fecha_AñoMes_planta")
    fig.update_xaxes(dtick="M1", tickformat="%b\n%Y")
    fig.update_layout(xaxis_tickangle=0)

    gg2.plotly_chart(fig, use_container_width=True)
    # ------------------------------------------------------------------------------------------------------------------
    with st.expander("Ver reportes piezas esmaltadas"):
        st.markdown("**Cantidad de Piezas Esmaltadas**")
        # Visualizando la tabla
        st.write("Cantidad de piezas esmaltadas por referencía, robot y turno.")
        visual_tabla_dinam(cantidad_piezas, "cantidad_piezas")

        st.markdown("**Cantidad de Esmalte Consumido**")
        st.write("Cantidad de esmalte utilizado por referencía, día, robot y turno.")
        # Visualizando la tabla
        visual_tabla_dinam(esmalte_cons.round(2), "esmalte_cons")

elif page == "Día a Día":
    st.header('Analisís del Día o del Periodo')
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
    # Selección de la fecha y el robot que se va analizar
    st.subheader("1. Selección de Periodo a Analizar")
    col1, col2 = st.columns(2)
    # Selección de la fecha
    with col1:
        st.markdown("**Opciones de Fecha**")
        sel_fecha = st.radio("¿Que periodo de tiempo desea analizar?",
                             ('Por día', 'Por rango de días'), key="fecha")

        # Opciones por día
        if sel_fecha == "Por día":
            sel_dia = st.date_input("¿Que dia desea analizar?", datetime.date.today(), key="dia")
            if sel_dia > datetime.date.today():
                st.error("Recuerda que el día seleccionado no puede ser superior al día actual")
                st.stop()
            st.info("Analizaras el día " + str(sel_dia))

        # Opciones por rango de fecha
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
                st.info("Analizaras un periodo de tiempo de " + str((sel_dia_fin - sel_dia_ini).days + 1) + " días.")

    # Selección del robot
    with col2:
        st.markdown("**Selección del Robot**")
        sel_robot = st.radio("¿Que Robot desea analizar?", ('Robot 1', 'Robot 2', 'Ambos'), key="robot")

        flag_download = False
        if st.checkbox("Descargar nuevamente"):
            flag_download = True
            st.legacy_caching.clear_cache()
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
    # Plotting th graph
    st.subheader("2. Graficar Información")
    descargar = st.checkbox("Graficar")
    if descargar is True:
        # Descargando la información
        with st.spinner('Descargando la información...'):
            if sel_fecha == "Por día":
                df, df2, salud_list, salud_datos, title = get_data_day(sel_robot, sel_dia, flag_download)
                text_dia = str(sel_dia)
                # ------------------------------------------------------------------------------------------------------
                # Finding missing dates for day only
                debug = False
                if debug is True:
                    periodo = pd.date_range(start=str(sel_dia) + ' 06:00:00',
                                            end=str(sel_dia + datetime.timedelta(days=1)) + ' 05:59:59', freq="s")
                    diferencias = periodo.difference(df.index)
                    st.write(diferencias)
                # ------------------------------------------------------------------------------------------------------
            elif sel_fecha == "Por rango de días":
                df, df2, salud_list, salud_datos, title = get_data_range(sel_robot, sel_dia_ini, sel_dia_fin,
                                                                         flag_download)
                text_dia = "from_" + str(sel_dia_ini) + "_to_" + str(sel_dia_fin)
            # ----------------------------------------------------------------------------------------------------------
            # Salud de los datos descargada
            c1, c2, c3 = st.columns(3)
            c1.success("Información descargada")
            c2.metric(label="Salud global de los datos", value="{:.2f}%".format(salud_datos))
            # ----------------------------------------------------------------------------------------------------------
        # Dibujando la grafica
        with st.spinner('Dibujando la información...'):
            if sel_robot == "Ambos":
                fig = plot_html_all(df, df2, title)
            else:
                fig = plot_html(df, title)
            st.plotly_chart(fig, use_container_width=True)
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
    # Analitica de la información cargada
    st.subheader("3. Analizar Información")
    analizar = st.checkbox("Analizar", key="Analizar")
    if analizar is True:
        if descargar is False:
            # Descargando la información
            with st.spinner('Descargando la información...'):
                if sel_fecha == "Por día":
                    df, df2, salud_list, salud_datos, title = get_data_day(sel_robot, sel_dia, flag_download)
                    text_dia = str(sel_dia)
                elif sel_fecha == "Por rango de días":
                    df, df2, salud_list, salud_datos, title = get_data_range(sel_robot, sel_dia_ini, sel_dia_fin,
                                                                             flag_download)
                    text_dia = "from_" + str(sel_dia_ini) + "_to_" + str(sel_dia_fin)
                # ----------------------------------------------------------------------------------------------------------
                # Salud de los datos descargada
                c1, c2, c3 = st.columns(3)
                c1.success("Información descargada")
                c2.metric(label="Salud global de los datos", value="{:.2f}%".format(salud_datos))
        # Analizando la información
        with st.spinner('Analizando la información...'):
            # Ejecuto la función que analiza el DF descargado
            if sel_robot == "Ambos":
                Analisis_df1 = find_analisis(df=df, robot="robot1", text_dia=text_dia, redownload=flag_download)
                Analisis_df2 = find_analisis(df=df2, robot="robot2", text_dia=text_dia, redownload=flag_download)
                Analisis_df_raw = pd.concat([Analisis_df1, Analisis_df2])
            else:
                # Definición del robot seleccionado
                Analisis_df_raw = find_analisis(df=df, robot=sel_robot.lower().replace(" ", ""), text_dia=text_dia,
                                            redownload=flag_download)
            # Visualizando la tabla
            visual_tabla_dinam(Analisis_df_raw, "analisis_table")
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
        # Reportes pre-establecidos de la data
        st.subheader("4.1. Reportes Consumos y Cantidades")
        # ----------------------------------------------------------------------------------------------------------
        # FILTROS para los analisis y reportes
        # ----------------------------------------------------------------------------------------------------------
        # Solo reporto los procesos que tuvieron algún consumo de esmalte.
        Analisis_df = Analisis_df_raw[Analisis_df_raw["Esmalte_Usado [Kg]"] != 0]

        # Solo reporto los procesos que finalizaron el día que estoy contando.
        Analisis_df = Analisis_df[(Analisis_df["Proceso_Completo"] == 1) | (Analisis_df["Proceso_Completo"] == -1)]

        # No cuento los procesos que son códigos de error
        Analisis_df = Analisis_df[~(Analisis_df["Referencia"].isin(error_list))]

        with st.expander("Ver reportes piezas fabricadas y esmalte consumido"):
            # ------------------------------------------------------------------------------------------------------
            # Tablas dinamicas de cantidad de piezas
            cantidad_piezas = Analisis_df.pivot_table(index=["Fecha_planta", "Robot", "Turno"],
                                                      values="Proceso_Completo",
                                                      columns="Referencia", aggfunc=len,
                                                      fill_value=0, margins=False)

            cantidad_piezas_grap = Analisis_df.pivot_table(index=["Fecha_planta", "Robot"],
                                                           values="Proceso_Completo",
                                                           columns="Referencia", aggfunc=len,
                                                           fill_value=0, margins=False).reset_index()

            st.markdown("**Cantidad de Piezas Esmaltadas**")
            st.write("Cantidad de piezas esmaltadas por referencía, día, robot y turno.")
            cantidad_piezas = cantidad_piezas.reset_index()
            cantidad_piezas.columns = list(map(str, cantidad_piezas.columns.values.tolist()))
            cantidad_piezas_grap.columns = list(map(str, cantidad_piezas_grap.columns.values.tolist()))

            # Visualizando la tabla
            visual_tabla_dinam(cantidad_piezas, "cantidad_piezas")
            # ------------------------------------------------------------------------------------------------------
            # Tablas dinamicas de horas por piezas
            horas_piezas = Analisis_df.pivot_table(index=["Fecha_planta", "Robot", "Turno"],
                                                   values="Tiempo_Estado [s]",
                                                   columns="Referencia", aggfunc='sum',
                                                   fill_value=0, margins=False) / 3600

            st.markdown("**Horas Totales Trabajadas**")
            st.write("Cantidad de Horas activas de la maquina por referencía, día, robot y turno.")
            horas_piezas = horas_piezas.reset_index()
            horas_piezas.columns = list(map(str, horas_piezas.columns.values.tolist()))

            # Visualizando la tabla
            visual_tabla_dinam(horas_piezas.round(2), "horas_piezas")
            # ------------------------------------------------------------------------------------------------------
            # Tablas dinamicas de esmalte consumido por pieza
            esmalte_cons = Analisis_df.pivot_table(index=["Fecha_planta", "Robot", "Turno"],
                                                   values="Esmalte_Usado [Kg]",
                                                   columns="Referencia", aggfunc='sum',
                                                   fill_value=0, margins=False)

            esmalte_cons_grap = Analisis_df.pivot_table(index=["Fecha_planta", "Robot"],
                                                        values="Esmalte_Usado [Kg]",
                                                        columns="Referencia", aggfunc='sum', fill_value=0,
                                                        margins=False).reset_index()

            st.markdown("**Cantidad de Esmalte Consumido**")
            st.write("Cantidad de esmalte utilizado por referencía, día, robot y turno.")
            esmalte_cons = esmalte_cons.reset_index()
            esmalte_cons.columns = list(map(str, esmalte_cons.columns.values.tolist()))
            esmalte_cons_grap.columns = list(map(str, esmalte_cons_grap.columns.values.tolist()))

            # Visualizando la tabla
            visual_tabla_dinam(esmalte_cons.round(2), "esmalte_cons")
            # ----------------------------------------------------------------------------------------------------------
            # ----------------------------------------------------------------------------------------------------------
            st.markdown("**Graficas de Piezas Fabricadas y Esmalte Consumido Total por Día**")
            st.markdown("Solo las referencias de productos")

            pp1, pp2 = st.columns(2)

            # Gráfica de total de piezas fabricadas por día objetivo de 700 piezas
            sum_cantidad = sum_procesos(cantidad_piezas_grap, "Piezas Esmaltadas")
            # -------------------------------------Plotly---------------------------------------------------------------
            fig = plot_total(sum_cantidad, salud_list, "Piezas Esmaltadas por Robot", "Piezas Esmaltadas [Und]",
                             flag=True)
            pp1.plotly_chart(fig, use_container_width=True)
            # ----------------------------------------------------------------------------------------------------------
            # Sumo el esmalte total en ambos o solo 1 robot
            sum_esmalte = sum_procesos(esmalte_cons_grap, "Esmalte Usado")

            x_column = sum_esmalte.columns.values.tolist()[1:]
            sum_esmalte["Total"] = 0
            for i in x_column:
                if i != "Total":
                    sum_esmalte["Total"] += sum_esmalte[i]

            # PLOTLY
            fig = plot_total(sum_esmalte, salud_list, "Esmalte Usado por Robot y Total", "Esmalte Usado [Kg]",
                             flag=False)
            pp2.plotly_chart(fig, use_container_width=True)
            # ----------------------------------------------------------------------------------------------------------
            # ----------------------------------------------------------------------------------------------------------
            # Reporte grafico por turno
            # ----------------------------------------------------------------------------------------------------------
            # Filtrado y selección
            st.markdown("**Graficas de Piezas Fabricadas y Esmalte Consumido por Turno en Cada Día**")
            sel_rob1 = st.selectbox("¿Que robot desea analizar?", list(cantidad_piezas["Robot"].unique()),
                                    0, key="rob01")
            # ----------------------------------------------------------------------------------------------------------
            # Cantidad de Piezas Esmaltadas
            # Filtro el DF por la selección realizada
            cantidad_piezas_filt2 = cantidad_piezas[cantidad_piezas["Robot"] == sel_rob1]

            # Organizo la data para poderla dibujar
            df_turno = pd.melt(frame=cantidad_piezas_filt2, id_vars=["Fecha_planta", "Robot", "Turno"],
                               var_name="Referencia", value_name="Cantidad")

            df_turno = df_turno.groupby(["Fecha_planta", "Robot", "Turno"]).sum().reset_index()

            ppp1, ppp2 = st.columns(2)
            # -------------------------------------Plotly---------------------------------------------------------------
            # Cantidad de piezas esmaltadas
            fig = plot_bar_turno(df=df_turno, salud=salud_list,
                                 title="Cantidad Piezas Esmaltadas por Día y Turno {}".format(sel_rob1.title()),
                                 ytitle='Piezas Esmaltadas [Und]')
            ppp1.plotly_chart(fig, use_container_width=True)
            # ----------------------------------------------------------------------------------------------------------
            # Cantidad de Esmalte usado
            # Filtro el DF por la selección realizada
            esmalte_cons_filt2 = esmalte_cons[esmalte_cons["Robot"] == sel_rob1]

            # Organizo la data para poderla dibujar
            df_turno = pd.melt(frame=esmalte_cons_filt2, id_vars=["Fecha_planta", "Robot", "Turno"],
                               var_name="Referencia", value_name="Cantidad")

            df_turno = df_turno.groupby(["Fecha_planta", "Robot", "Turno"]).sum().reset_index()
            # -------------------------------------Plotly---------------------------------------------------------------
            # Cantidad de Esmalte esmaltadas
            fig = plot_bar_turno(df=df_turno, salud=salud_list,
                                 title="Cantidad Esmalte Consumido por Día y Turno {}".format(sel_rob1.title()),
                                 ytitle='Esmalte Consumido [Kg]')
            ppp2.plotly_chart(fig, use_container_width=True)
            # ----------------------------------------------------------------------------------------------------------
            # ----------------------------------------------------------------------------------------------------------
            # Reporte grafico por referencia
            # ----------------------------------------------------------------------------------------------------------
            # ----------------------------------------------------------------------------------------------------------
            # Graficas de los reportes generados
            st.markdown("**Graficas de Piezas Fabricadas y Esmalte Consumido por Robot, Referencia y Día**")

            p1, p2 = st.columns(2)

            # Filtrado y selección
            sel_rob0 = p1.selectbox("¿Que robot desea analizar?", ["Ambos Robots"] +
                                    list(cantidad_piezas["Robot"].unique()), 0, key="rob00")

            sel_turno = p2.selectbox("¿Que turno desea analizar?", ["Día Completo"] +
                                     list(cantidad_piezas["Turno"].unique()), 0, key="Turno")

            # Filtrado por el turno y el robot
            if sel_turno == "Día Completo":
                # Sin información de turnos
                if sel_rob0 != "Ambos Robots":
                    cantidad_piezas_filt = cantidad_piezas_grap[cantidad_piezas_grap["Robot"] == sel_rob0]
                    esmalte_cons_filt = esmalte_cons_grap[esmalte_cons_grap["Robot"] == sel_rob0]
                else:
                    cantidad_piezas_filt = cantidad_piezas_grap.copy()
                    esmalte_cons_filt = esmalte_cons_grap.copy()
            else:
                # Con información de turno
                cantidad_piezas_turno = cantidad_piezas[cantidad_piezas["Turno"] == sel_turno]
                esmalte_cons_turno = esmalte_cons[esmalte_cons["Turno"] == sel_turno]

                cantidad_piezas_turno.drop("Turno", inplace=True, axis=1)
                esmalte_cons_turno.drop("Turno", inplace=True, axis=1)

                if sel_rob0 != "Ambos Robots":
                    cantidad_piezas_filt = cantidad_piezas_turno[cantidad_piezas_turno["Robot"] == sel_rob0]
                    esmalte_cons_filt = esmalte_cons_turno[esmalte_cons_turno["Robot"] == sel_rob0]
                else:
                    cantidad_piezas_filt = cantidad_piezas_turno.copy()
                    esmalte_cons_filt = esmalte_cons_turno.copy()
            # -------------------------------------Plotly---------------------------------------------------------------
            # Cantidad de piezas esmaltadas
            fig = plot_bar_referencia(df=cantidad_piezas_filt, salud=salud_list,
                                      title="Cantidad de Piezas Esmaltadas {} y Turno {}".format(sel_rob0.title(),
                                                                                                 sel_turno),
                                      ytitle='Piezas Esmaltadas [Und]')

            p1.plotly_chart(fig, use_container_width=True)
            # -------------------------------------Plotly---------------------------------------------------------------
            # Cantidad de esmalte usado
            fig = plot_bar_referencia(df=esmalte_cons_filt, salud=salud_list,
                                      title="Esmalte Consumido por Referencia {} y Turno {}".format(sel_rob0.title(),
                                                                                                    sel_turno),
                                      ytitle='Esmalte Consumido [Kg]')

            p2.plotly_chart(fig, use_container_width=True)
            # ----------------------------------------------------------------------------------------------------------
            # Programa para reporte manual de tablas dinamicas usando pivot_ui
            if st.checkbox("Reporte Manual"):
                t = pivot_ui(Analisis_df)
                with open(t.src) as t:
                    components.html(t.read(), width=1200, height=600, scrolling=True)

# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
        # Reportes tiempos muertos
        st.subheader("4.2. Reportes Tiempos Muertos")
        # ----------------------------------------------------------------------------------------------------------
        # ANALIZANDO tiempos muertos entre procesos de esmaltados
        # ----------------------------------------------------------------------------------------------------------
        with st.expander("Ver reportes de tiempos muertos"):
            var_robot = Analisis_df_raw["Robot"].unique()

            # Definiendo el dataset total de tiempos
            Analisis_tiempos = pd.DataFrame(columns=['Fecha_all', 'Fecha', 'Hora', 'Tiempo_Muerto [s]', 'Robot'])

            for elem in var_robot:
                # Filtrando el analisis por robot1
                Analisis_df_raw_robot = Analisis_df_raw[Analisis_df_raw["Robot"] == elem].copy()

                #Convertiendo a string
                Analisis_df_raw_robot.loc[:, "Fecha"] = Analisis_df_raw_robot["Fecha"].apply(lambda x: str(x))
                Analisis_df_raw_robot.loc[:, "Hora"] = Analisis_df_raw_robot["Hora"].apply(lambda x: str(x))

                # Creando la columna con fecha y hora Inicial del proceso
                Fecha_ini = Analisis_df_raw_robot["Fecha"] + ", " + Analisis_df_raw_robot["Hora"]

                # Convirtiendo a tipo datetime
                Fecha_ini = pd.to_datetime(Fecha_ini, format="%Y-%m-%d, %H:%M:%S")

                # Convirtiendo la duración del esmaltado en un timedelta.
                time_delta = pd.to_timedelta(Analisis_df_raw_robot["Tiempo_Esmaltado [s]"], unit='s')

                # Calculando la fecha final
                Fecha_final = Fecha_ini + time_delta

                # Cortando las listas para restar la fecha final a la fecha inicial posterior
                Fecha_ini = Fecha_ini[1:]
                Fecha_final = Fecha_final[:-1]

                # Calculando tiempos muertos entre 2 procesos
                tiempo_muerto = []
                for i in range(len(Fecha_ini)):
                    tiempo_muerto.append((Fecha_ini.iloc[i] - Fecha_final.iloc[i]).total_seconds())

                # Descomponiendo la fecha_final en fecha y tiempo
                Hora_final = Fecha_final.apply(lambda x: x.time())
                Fecha = Fecha_final.apply(lambda x: x.date())

                # Creando el df de tiempos muertos
                Analisis_tiempos_aux = pd.DataFrame(list(zip(Fecha_final, Fecha, Hora_final, tiempo_muerto)),
                                                    columns=['Fecha_all', 'Fecha', 'Hora', 'Tiempo_Muerto [s]'])
                # Agregando el robot al df
                Analisis_tiempos_aux["Robot"] = elem

                # Guardando resultados en el dataset final de tiempos
                Analisis_tiempos = pd.concat([Analisis_tiempos, Analisis_tiempos_aux])

            # ----------------------------------------------------------------------------------------------------------
            # Plotly
            title = 'Tiempo Muertos Celula de Esmaltado'
            fig = plot_tiempo_muerto(Analisis_tiempos, title)
            st.plotly_chart(fig, use_container_width=True)
            # ----------------------------------------------------------------------------------------------------------
            # Filtro los datos mayores al tiempo maximo de traslación
            transfer_time = st.number_input("¿Cuanto es el tiempo máximo de translación [s]?", 45)

            m1, m2 = st.columns(2)
            with m1:
                # Visualizando la tabla
                visual_tabla_dinam(Analisis_tiempos[['Fecha', 'Hora', 'Tiempo_Muerto [s]',
                                                     'Robot']].round(2), "tiempos_m")
            with m2:
                # Filtro el df para tener solo aquellos datos mayores al tiempo de transfer
                Analisis_tiempos_filter = Analisis_tiempos[Analisis_tiempos['Tiempo_Muerto [s]'] > transfer_time].copy()

                # Elimino el tiempo muerto
                Analisis_tiempos_filter.loc[:, 'Tiempo_Muerto [s]'] -= transfer_time

                # Sumo y convierto a minutos
                bar_total_muerto = Analisis_tiempos_filter.groupby(by="Robot").sum()/60
                bar_total_muerto.reset_index(inplace=True)

                # ------------------------------------------------------------------------------------------------------
                title_plot = "Acumulado Tiempo Muerto"
                fig = plot_bar_acum_tiempo_muerto(bar_total_muerto, title_plot)
                st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
        # Analisis de la dispersión de esmaltado
        st.subheader("4.3. Dispersión Esmaltado")
        with st.expander("Ver dispersión esmaltado"):
            # Dispersión del esmalte usado
            st.markdown("**Dispersión Esmaltado en el Tiempo**")
            sss1, sss2 = st.columns((3, 1))

            # Filtrado y selección
            rob = Analisis_df["Robot"].unique()
            sel_rob = sss2.selectbox("¿Que robot desea analizar?", rob, 0, key="rob0")
            data = Analisis_df[Analisis_df["Robot"] == sel_rob]
            # -------------------------------------Plotly-----------------------------------------------------------
            # Grafica de dispersion del esmalte usado
            fig = px.box(data, x="Fecha_planta", y="Esmalte_Usado [Kg]", color="Referencia", template="seaborn",
                         orientation="v")

            fig.update_traces(marker=dict(size=2))
            fig.update_xaxes(type='category')
            fig.update_layout(height=700, width=700, legend=dict(orientation="v"))
            fig.update_layout(template="seaborn", title="Esmalte Usado por Referencia [Kg] en el " + sel_rob)

            # Set x-axis and y-axis title
            fig['layout']['xaxis']['title'] = 'Fechas'
            fig['layout']['yaxis']['title'] = 'Esmalte Usado'
            fig.update_xaxes(showline=True, linewidth=0.5, linecolor='black')
            fig.update_yaxes(showline=True, linewidth=0.5, linecolor='black')

            sss1.plotly_chart(fig, use_container_width=True)
# ----------------------------------------------------------------------------------------------------------------------
            # Dispersion del esmaltado total en el periodo
            st.markdown("**Dispersión Esmaltado por Robot**")

            # Selección y filtrado de la base de datos
            dt = Analisis_df["Fecha_planta"].unique()

            ss1, ss2 = st.columns((3, 1))
            with ss2.form("Filtros"):
                selec_dt1 = st.multiselect("¿Que fecha desea analizar?", dt, dt[:], key="dt1")
                st.form_submit_button("Filtrar")

            # Fitrado solo procesos completos
            report_df1 = Analisis_df[Analisis_df["Fecha_planta"].isin(selec_dt1)]
            # -------------------------------------Plotly-----------------------------------------------------------
            # Grafica de dispersión del esmalte
            fig = px.box(report_df1, x="Robot", y="Esmalte_Usado [Kg]", color="Referencia",
                         points="outliers",  # "all"
                         notched=False, template="seaborn")  # used notched shape

            fig.update_traces(marker=dict(size=2))
            fig.update_xaxes(type='category')
            fig.update_layout(height=700, width=700, legend=dict(orientation="v"))
            fig.update_layout(template="seaborn", title="Esmalte Usado por Referencia [Kg]")

            # Set x-axis and y-axis title
            fig['layout']['xaxis']['title'] = 'Robots'
            fig['layout']['yaxis']['title'] = 'Esmalte Usado'
            fig.update_xaxes(showline=True, linewidth=0.5, linecolor='black')
            fig.update_yaxes(showline=True, linewidth=0.5, linecolor='black')

            ss1.plotly_chart(fig, use_container_width=True)
            # ------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
elif page == "Online":
    st.header("En construcción - Ventana para ver el estado en vivo")

    # Placeholder definition
    start_button = st.empty()
    placeholder = st.empty()

    # Current day
    sel_dia = datetime.date.today()

    if start_button.button('Ver en Vivo', key='start'):
        with st.expander("Ver analisis del proceso"):
            text1_holder = st.empty()
            r1_holder = st.empty()
            text2_holder = st.empty()
            r2_holder = st.empty()

        # Variables initialization
        start_button.empty()
        initial_time = 10
        orig_size_1 = 60 * initial_time
        cont = 0

        # Initial plot
        # start_time = time.time()
        live_pd_r1, live_pd_r2, fig1 = sql_plot_live(time=60 * initial_time, day=str(sel_dia))
        placeholder.plotly_chart(fig1, use_container_width=True)
        # print("---initial_plot %s seconds ---" % (time.time() - start_time))

        # Run when activated
        if st.button('Detener', key='stop'):
            pass
        while True:
            # Robot 1
            # start_time = time.time()
            r1_update = sql_connect_live(time=60, day=str(sel_dia), database='robot1',
                                         table="robot1")
            r1_update = fecha_format(r1_update)
            r1_update["robot"] = "robot1"
            live_pd_r1 = pd.concat([live_pd_r1, r1_update]).drop_duplicates()

            # Robot 2
            r2_update = sql_connect_live(time=60 + 20, day=str(sel_dia), database='robot2',
                                         table="robot2")
            r2_update = fecha_format(r2_update)
            r2_update["robot"] = "robot2"
            live_pd_r2 = pd.concat([live_pd_r2, r2_update]).drop_duplicates()

            # Setting of the same period of time for both robots
            final_size_1 = live_pd_r1.shape[0]
            live_pd_r1 = live_pd_r1.iloc[(final_size_1 - orig_size_1):, :]
            live_pd_r2 = live_pd_r2.loc[live_pd_r1.index[0]:live_pd_r1.index[-1], :]

            # Plotting
            # Defining the title and filename for saving the plots
            title = "En vivo Robots de Esmaltado Día " + str(sel_dia)
            fig = plot_html_all(live_pd_r1, live_pd_r2, title)
            placeholder.plotly_chart(fig, use_container_width=True)
            # print("---plot %s seconds ---" % (time.time() - start_time))
            # ----------------------------------------------------------------------------------------------------------
            # Analisis en tiempo real
            start_time = time.time()
            Analisis_r1 = find_analisis(df=live_pd_r1, robot="robot1", text_dia="En Vivo", redownload=True)
            Analisis_r2 = find_analisis(df=live_pd_r2, robot="robot2", text_dia="En Vivo", redownload=True)
            # Analisis_live = pd.concat([Analisis_r1, Analisis_r2])
            print("---Analisis %s seconds ---" % (time.time() - start_time))

            # Visualizando la tabla
            # Robot 1
            text1_holder.markdown("**Información Robot 1**")
            with r1_holder:
                visual_tabla_dinam(Analisis_r1, "r1" + str(cont))

            # Robot 2
            text2_holder.markdown("**Información Robot 2**")
            with r2_holder:
                visual_tabla_dinam(Analisis_r2, "r2" + str(cont))
            # Aumento contador para variar el key de la visualización
            cont += 1

            # Wait x seconds before updating
            time.sleep(30)
            print(cont)
            st.legacy_caching.clear_cache()

# ----------------------------------------------------------------------------------------------------------------------
st.sidebar.header("Acerca de la App")
st.sidebar.markdown("**Creado por:**")
st.sidebar.write("Juan Felipe Monsalvo Salazar")
st.sidebar.write("jmonsalvo@corona.com.co")
st.sidebar.markdown("**Creado el:** 14/01/2021")
