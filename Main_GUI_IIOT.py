# Python File for streamlit tools
# GUI APP for IIOT | Corona
# 21-September-2021
# ----------------------------------------------------------------------------------------------------------------------
# Libraries
import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from pivottablejs import pivot_ui
from st_aggrid import AgGrid, GridOptionsBuilder

# Internal Function
from Analysis_Function import analitica_esmalte, visual_tabla_dinam
from SQL_Function import sql_plot, sql_plot_all
# ----------------------------------------------------------------------------------------------------------------------
# Streamlit Setting
st.set_page_config(page_title="IIOT - Corona",
                   initial_sidebar_state="collapsed",
                   page_icon="📈",
                   layout="wide")

tabs = ["Celula de Esmaltado"]
page = st.sidebar.radio("Tabs", tabs)
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# Initial page
st.title(' 📈 IIOT - Corona 🤖')

if page == "Celula de Esmaltado":
    st.header('Celula Robotizada de Esmaltado Girardota')
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
                if sel_robot == "Ambos":
                    robot1, robot2, fig = sql_plot_all(tipo="day", day=str(sel_dia))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    df, fig = sql_plot(tipo="day", day=str(sel_dia), database=tabla_sql, table=tabla_sql)
                    st.plotly_chart(fig, use_container_width=True)

            # Por rango de fecha
            elif sel_fecha == "Por rango de días":
                if sel_robot == "Ambos":
                    robot1, robot2, fig = sql_plot_all(tipo="rango", ini=str(sel_dia_ini), day=str(sel_dia_fin))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    df, fig = sql_plot(tipo="rango", ini=str(sel_dia_ini), day=str(sel_dia_fin),
                                       database=tabla_sql, table=tabla_sql)
                    st.plotly_chart(fig, use_container_width=True)
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
        # Analitica de la información cargada
        st.subheader("3. Analizar Información")
        if st.checkbox("Analizar", key="Analizar"):
            with st.spinner('Analizando la información...'):

                # Ejecuto la función que analisa el DF descargado
                if sel_robot == "Ambos":
                    Analisis_df1 = analitica_esmalte(robot1)
                    Analisis_df2 = analitica_esmalte(robot2)
                    Analisis_df = pd.concat([Analisis_df1, Analisis_df2])
                else:
                    Analisis_df = analitica_esmalte(df)

                # ------------------------------------------------------------------------------------------------------
                # Definiendo la tabla de visualización
                # ------------------------------------------------------------------------------------------------------
                gb = GridOptionsBuilder.from_dataframe(Analisis_df)

                gb.configure_side_bar()
                gb.configure_default_column(groupable=True, value=True, enableRowGroup=True,
                                            aggFunc="sum",editable=False)
                gridOptions = gb.build()

                tabla = AgGrid(Analisis_df,
                               editable=False, sortable=True, filter=True, resizable=True, defaultWidth=5,
                               fit_columns_on_grid_load=False,
                               theme="streamlit",  # "light", "dark", "blue", "fresh", "material"
                               key='analisis_table', reload_data=True,
                               gridOptions=gridOptions, enable_enterprise_modules=True)
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
            # Reportes pre-establecidos de la data
            st.subheader("4. Reportes Consumos y Cantidades")
            if st.checkbox("Reportes Pre-Establecidos"):
                # ------------------------------------------------------------------------------------------------------
                # Tablas dinamicas de cantidad de piezas
                cantidad_piezas = Analisis_df.pivot_table(index=["Fecha_planta", "Robot", "Turno"],
                                                          values="Proceso_Completo",
                                                          columns="Referencia", aggfunc='sum',
                                                          fill_value=0, margins=False)

                cantidad_piezas_grap = Analisis_df.pivot_table(index=["Fecha_planta", "Robot"],
                                                               values="Proceso_Completo",
                                                               columns="Referencia", aggfunc='sum',
                                                               fill_value=0, margins=False).reset_index()

                st.markdown("**Cantidad de Piezas Esmaltadas**")
                st.write("Cantidad de piezas esmaltadas por referencía, día, robot y turno.")
                cantidad_piezas = cantidad_piezas.reset_index()
                cantidad_piezas.columns = list(map(str, cantidad_piezas.columns.values.tolist()))

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
                horas_piezas.columns = list(map(str,horas_piezas.columns.values.tolist()))

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

                # Visualizando la tabla
                visual_tabla_dinam(esmalte_cons.round(2), "esmalte_cons")
                # ------------------------------------------------------------------------------------------------------
                # Graficas de los reportes generados
                with st.expander("Ver graficas"):
                    p1, p2 = st.columns(2)
                    iter_colum = cantidad_piezas_grap.columns.values.tolist()[2:]

                    # -------------------------------------Plotly-------------------------------------------------------
                    # Cantidad de piezas esmaltadas
                    fig = go.Figure()
                    for elem in iter_colum:
                        fig.add_trace(go.Bar(
                            x=cantidad_piezas_grap["Fecha_planta"],
                            y=cantidad_piezas_grap[int(elem)],
                            # text=cantidad_piezas_grap[int(elem)],textposition='auto',
                            name=elem))

                    # Here we modify the tickangle of the xaxis, resulting in rotated labels.
                    fig.update_layout(barmode='group', bargap=0.1,  bargroupgap=0.02, xaxis_tickangle=0)
                    fig.update_layout(height=500, width=700, legend=dict(orientation="v"))
                    fig.update_layout(template="seaborn", title="Cantidad de Piezas Esmaltadas")

                    # Set x-axis and y-axis title
                    fig['layout']['xaxis']['title'] = 'Fecha'
                    fig['layout']['yaxis']['title'] = 'Piezas Esmaltadas'

                    p1.plotly_chart(fig, use_container_width=True)

                    # -------------------------------------Plotly-------------------------------------------------------
                    # Cantidad de esmalte usado
                    iter_colum = esmalte_cons_grap.columns.values.tolist()[2:]
                    fig = go.Figure()
                    for elem in iter_colum:
                        fig.add_trace(go.Bar(
                            x=esmalte_cons_grap["Fecha_planta"],
                            y=np.round(esmalte_cons_grap[int(elem)], 2),
                            # text=np.round(esmalte_cons_grap[int(elem)],2),textposition='auto',
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

            # ----------------------------------------------------------------------------------------------------------
            # Programa para reporte manual de tablas dinamicas usando pivot_ui
            if st.checkbox("Reporte Manual"):
                t = pivot_ui(Analisis_df)
                with open(t.src) as t:
                    components.html(t.read(), width=1200, height=600, scrolling=True)
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
            # Analisis de la dispersión de esmaltado
            st.subheader("5. Dispersión Esmaltado")

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

                ss1.plotly_chart(fig, use_container_width=True)
                # ------------------------------------------------------------------------------------------------------
                # Dispersión del esmalte usado
                st.markdown("**Dispersión Esmaltado en el Tiempo**")
                sss1, sss2 = st.columns((3,1))

                # Filtrado y selección
                sel_rob = sss2.selectbox("¿Que robot desea analizar?", rob, 0, key="rob0")
                data = Analisis_df[Analisis_df["Proceso_Completo"]== 1] # Solo procesos completos
                data = data[data["Robot"] == sel_rob]

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

                sss1.plotly_chart(fig, use_container_width=True)
# ----------------------------------------------------------------------------------------------------------------------
st.sidebar.header("Acerca de la App")
st.sidebar.markdown("**Creado por:**")
st.sidebar.write("Juan Felipe Monsalvo Salazar")
st.sidebar.write("jmonsalvo@corona.com.co")
st.sidebar.markdown("**Creado el:** 21/09/2021")
