# Python File for streamlit tools
# Sales Baños y Cocna
# 03-August-2021
# ----------------------------------------------------------------------------------------------------------------------
# Libraries
import datetime
import numpy as np
import pandas as pd

import streamlit as st
import streamlit.components.v1 as components
from pivottablejs import pivot_ui

from st_aggrid import AgGrid, DataReturnMode, GridUpdateMode, GridOptionsBuilder

import plotly.express as px
import plotly.graph_objects as go

# Internal Function
from SQL_Function import sql_plot, sql_plot_all, sql_plot_presecadero
from Analysis_Function import DF_Analitica_Esmalte
# ----------------------------------------------------------------------------------------------------------------------
# Streamlit Setting
st.set_page_config(page_title="IIOT - Corona",
                   initial_sidebar_state="collapsed",
                   page_icon="📈",
                   layout="wide")

tabs = ["Celula de Esmaltado", "Pre-Secadero"]
page = st.sidebar.radio("Tabs", tabs)
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
