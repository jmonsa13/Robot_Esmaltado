# Python File for streamlit tools
# GUI APP for IIOT | Corona
# 21-September-2021
# ----------------------------------------------------------------------------------------------------------------------
# Libraries
import datetime
import time

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from st_aggrid import AgGrid

from pivottablejs import pivot_ui

# Internal Function
from Analysis_Function import find_analisis, visual_tabla_dinam, sum_procesos
from Plot_Function import plot_bar, plot_bar_turno, plot_line, plot_html_all
from SQL_Function import sql_plot, sql_plot_all, sql_plot_live, sql_connect_live, fecha_format

# ----------------------------------------------------------------------------------------------------------------------
# Streamlit Setting
st.set_page_config(page_title="IIOT - Corona",
                   initial_sidebar_state="collapsed",
                   page_icon="📈",
                   layout="wide")

tabs = ["Celula de Esmaltado", "Online"]
page = st.sidebar.radio("Tabs", tabs)
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# Initial page
st.title(' 📈 IIOT - Corona 🤖')

if page == "Celula de Esmaltado":
    st.header('Celula Robotizada de Esmaltado Girardota')

    df = pd.DataFrame()
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
    # Selección de la fecha y el robot que se va analizar
    st.subheader("1. Selección de Data a Analizar")
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
    # Conexión a la base de datos SQL, descarga y grafica
    st.subheader("2. Descargar y Graficar Información")
    if st.checkbox("Descargar y Graficar Información"):
        with st.spinner('Descargando la información y dibujandola...'):

            # Definición del robot seleccionado
            if sel_robot == "Robot 1":
                tabla_sql = "robot1"
            elif sel_robot == "Robot 2":
                tabla_sql = "robot2"

            # Definición del rango de fecha seleccionado
            # Por día
            if sel_fecha == "Por día":
                text_dia = str(sel_dia)
                if sel_robot == "Ambos":
                    robot1, robot2, fig = sql_plot_all(tipo="day_planta", day=str(sel_dia), redownload=flag_download)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    df, fig = sql_plot(tipo="day_planta", day=str(sel_dia), database=tabla_sql, table=tabla_sql,
                                       redownload=flag_download)
                    st.plotly_chart(fig, use_container_width=True)

            # Por rango de fecha
            elif sel_fecha == "Por rango de días":
                text_dia = "from_" + str(sel_dia_ini) + "_to_" + str(sel_dia_fin)
                if sel_robot == "Ambos":
                    robot1, robot2, fig = sql_plot_all(tipo="rango_planta", ini=str(sel_dia_ini), day=str(sel_dia_fin),
                                                       redownload=flag_download)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    df, fig = sql_plot(tipo="rango_planta", ini=str(sel_dia_ini), day=str(sel_dia_fin),
                                       database=tabla_sql, table=tabla_sql, redownload=flag_download)
                    st.plotly_chart(fig, use_container_width=True)
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
        # Analitica de la información cargada
        st.subheader("3. Analizar Información")
        if st.checkbox("Analizar", key="Analizar"):
            with st.spinner('Analizando la información...'):
                # Ejecuto la función que analisa el DF descargado
                if sel_robot == "Ambos":
                    Analisis_df1 = find_analisis(df=robot1, robot="robot1", text_dia=text_dia, redownload=flag_download)
                    Analisis_df2 = find_analisis(df=robot2, robot="robot2", text_dia=text_dia, redownload=flag_download)
                    Analisis_df = pd.concat([Analisis_df1, Analisis_df2])
                else:
                    Analisis_df = find_analisis(df=df, robot=tabla_sql, text_dia=text_dia, redownload=flag_download)

                # Visualizando la tabla
                visual_tabla_dinam(Analisis_df, "analisis_table")
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
            # Reportes pre-establecidos de la data
            st.subheader("4. Reportes Consumos y Cantidades")
            # ----------------------------------------------------------------------------------------------------------
            # FILTROS para los analisis y reportes
            # ----------------------------------------------------------------------------------------------------------
            # Solo reporto los procesos que tuvieron algun consumo de esmalte.
            Analisis_df = Analisis_df[Analisis_df["Esmalte_Usado [Kg]"] != 0]

            # Solo reporto los procesos que finalizaron el día que estoy contando.
            Analisis_df = Analisis_df[(Analisis_df["Proceso_Completo"] == 1) | (Analisis_df["Proceso_Completo"] == -1)]

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
                # ------------------------------------------------------------------------------------------------------
                # Graficas de los reportes generados
                #with st.expander("Ver graficas"):
                st.markdown("**Graficas de Piezas Fabricadas y Esmalte Consumido por Robot, Referencia y Día**")

                p1, p2 = st.columns(2)

                # Filtrado y selección
                sel_rob0 = p1.selectbox("¿Que robot desea analizar?", ["Ambos"] +
                                        list(cantidad_piezas["Robot"].unique()), 0, key="rob00")

                sel_turno = p2.selectbox("¿Que turno desea analizar?", ["Día Completo"] +
                                         list(cantidad_piezas["Turno"].unique()), 0, key="Turno")

                # Filtrado por el turno y el robot
                if sel_turno == "Día Completo":
                    # Sin información de turnos
                    if sel_rob0 != "Ambos":
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

                    if sel_rob0 != "Ambos":
                        cantidad_piezas_filt = cantidad_piezas_turno[cantidad_piezas_turno["Robot"] == sel_rob0]
                        esmalte_cons_filt = esmalte_cons_turno[esmalte_cons_turno["Robot"] == sel_rob0]
                    else:
                        cantidad_piezas_filt = cantidad_piezas_turno.copy()
                        esmalte_cons_filt = esmalte_cons_turno.copy()
                # -------------------------------------Plotly-------------------------------------------------------
                # Cantidad de piezas esmaltadas
                fig = plot_bar(df=cantidad_piezas_filt, title="Cantidad de Piezas Esmaltadas",
                               ytitle='Piezas Esmaltadas')

                p1.plotly_chart(fig, use_container_width=True)
                # -------------------------------------Plotly-------------------------------------------------------
                # Cantidad de esmalte usado
                fig = plot_bar(df=esmalte_cons_filt, title="Esmalte Consumido por Referencia",
                               ytitle='Esmalte Consumido [Kg]')

                p2.plotly_chart(fig, use_container_width=True)
                #--------------------------------------------------------------------------------------------------
                # Reporte grafico por turno
                #--------------------------------------------------------------------------------------------------
                # Filtrado y selección
                st.markdown("**Graficas de Piezas Fabricadas y Esmalte Consumido por Turno en Cada Día**")
                sel_rob1 = st.selectbox("¿Que robot desea analizar?", list(cantidad_piezas["Robot"].unique()),
                                        0, key="rob01")
                #--------------------------------------------------------------------------------------------------
                # Cantidad de Piezas Esmaltadas
                # Filtro el DF por la selección realizada
                cantidad_piezas_filt2 = cantidad_piezas[cantidad_piezas["Robot"] == sel_rob1]

                # Organizo la data para poderla dibujar
                df_turno = pd.melt(frame=cantidad_piezas_filt2, id_vars=["Fecha_planta", "Robot", "Turno"],
                               var_name="Referencia", value_name="Cantidad")

                df_turno = df_turno.groupby(["Fecha_planta", "Robot", "Turno"]).sum().reset_index()

                ppp1, ppp2 = st.columns(2)
                # -------------------------------------Plotly-------------------------------------------------------
                # Cantidad de piezas esmaltadas
                fig = plot_bar_turno(df=df_turno, title="Cantidad Piezas Esmaltadas por Día y Turno",
                                     ytitle='Cantidad Piezas Esmaltadas')
                ppp1.plotly_chart(fig, use_container_width=True)
                #--------------------------------------------------------------------------------------------------
                # Cantidad de Esmalte usado
                # Filtro el DF por la selección realizada
                esmalte_cons_filt2 = esmalte_cons[esmalte_cons["Robot"] == sel_rob1]

                # Organizo la data para poderla dibujar
                df_turno = pd.melt(frame=esmalte_cons_filt2, id_vars=["Fecha_planta", "Robot", "Turno"],
                               var_name="Referencia", value_name="Cantidad")

                df_turno = df_turno.groupby(["Fecha_planta", "Robot", "Turno"]).sum().reset_index()
                # -------------------------------------Plotly-------------------------------------------------------
                # Cantidad de piezas esmaltadas
                fig = plot_bar_turno(df=df_turno, title="Cantidad Esmalte Consumido por Día y Turno",
                                     ytitle='Esmalte Consumido [Kg]')
                ppp2.plotly_chart(fig, use_container_width=True)
                # --------------------------------------------------------------------------------------------------
                # --------------------------------------------------------------------------------------------------
                st.markdown("**Graficas de Piezas Fabricadas y Esmalte Consumido Total por Día**")
                st.markdown("Solo las referencias de productos")

                pp1, pp2 = st.columns(2)

                # Grafica de total de piezas fabricadas por día objetivo de 700 piezas
                # ME QUEDO SOLO CON LAS REFERENCIAS REALES DEL PROCESO
                error_list = [0, 101, 126]

                cantidad_piezas_grap = cantidad_piezas_grap.loc[:, ~cantidad_piezas_grap.columns.isin(error_list)]
                sum_cantidad = sum_procesos(cantidad_piezas_grap, "Piezas Esmaltadas")

                # -------------------------------------Plotly-------------------------------------------------------
                fig = plot_line(sum_cantidad, "Piezas Esmaltadas por Robot", "Piezas Esmaltadas [Und]", flag=True)
                pp1.plotly_chart(fig, use_container_width=True)
                #--------------------------------------------------------------------------------------------------
                # Sumo el esmalte total en ambos o solo 1 robot
                esmalte_cons_grap = esmalte_cons_grap.loc[:, ~esmalte_cons_grap.columns.isin(error_list)]
                sum_esmalte = sum_procesos(esmalte_cons_grap, "Esmalte Usado")

                x_column = sum_esmalte.columns.values.tolist()[1:]
                sum_esmalte["Total"] = 0
                for i in x_column:
                    if i != "Total":
                        sum_esmalte["Total"] += sum_esmalte[i]

                # PLOTLY
                fig = plot_line(sum_esmalte, "Esmalte Usado por Robot y Total", "Esmalte Usado [Kg]")
                pp2.plotly_chart(fig, use_container_width=True)
                # ------------------------------------------------------------------------------------------------------
                # Programa para reporte manual de tablas dinamicas usando pivot_ui
                if st.checkbox("Reporte Manual"):
                    t = pivot_ui(Analisis_df)
                    with open(t.src) as t:
                        components.html(t.read(), width=1200, height=600, scrolling=True)
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
            # Analisis de la dispersión de esmaltado
            st.subheader("5. Dispersión Esmaltado")
            with st.expander("Ver dispersión esmaltado"):
                # Dispersión del esmalte usado
                st.markdown("**Dispersión Esmaltado en el Tiempo**")
                sss1, sss2 = st.columns((3,1))

                # Filtrado y selección
                rob = Analisis_df["Robot"].unique()
                sel_rob = sss2.selectbox("¿Que robot desea analizar?", rob, 0, key="rob0")
                data = Analisis_df[Analisis_df["Robot"] == sel_rob]
                # -------------------------------------Plotly-----------------------------------------------------------
                # Grafica de dispersion del esmalte usado
                fig = px.box(data, x="Fecha_planta", y="Esmalte_Usado [Kg]", color="Referencia",template="seaborn",
                             orientation="v")

                fig.update_traces(marker=dict(size=2))
                fig.update_xaxes(type='category')
                fig.update_layout(height=700, width=700, legend=dict(orientation="v"))
                fig.update_layout(template="seaborn", title="Esmalte Usado por Referencia [Kg] en el "+ sel_rob)

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

                ss1, ss2 = st.columns((3,1))
                with ss2.form("Filtros"):
                    selec_dt1 =st.multiselect("¿Que fecha desea analizar?", dt, dt[:], key="dt1")
                    st.form_submit_button("Filtrar")

                # Fitrado solo procesos completos
                report_df1 = Analisis_df[Analisis_df["Fecha_planta"].isin(selec_dt1)]
                # -------------------------------------Plotly-----------------------------------------------------------
                # Grafica de dispersión del esmalte
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
                fig.update_xaxes(showline=True, linewidth=0.5, linecolor='black')
                fig.update_yaxes(showline=True, linewidth=0.5, linecolor='black')

                ss1.plotly_chart(fig, use_container_width=True)
                # ------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
if page == "Online":
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
        live_pd_r1 = pd.DataFrame()
        live_pd_r2 = pd.DataFrame()
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
            #Analisis_live = pd.concat([Analisis_r1, Analisis_r2])
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
st.sidebar.markdown("**Creado el:** 21/09/2021")
