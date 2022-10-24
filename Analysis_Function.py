# Python File function for streamlit tools
# Analysis function for IIOT | Colceramica
# 21-September-2021
# ----------------------------------------------------------------------------------------------------------------------
# Libraries
import datetime
import os
import sys

import numpy as np
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder


# ----------------------------------------------------------------------------------------------------------------------
# Function definition
def sum_procesos(df, name, column="Fecha_planta"):
    """
    Función para sumar los valores de las tablas dinamicas generadas por fecha
    INPUT:
        df: data frame pivotadeado a sumar
        name: Nombre a poner en la columna
        column: Nombre de la columna donde se realizara la sumatoria
    OUTPUT:
        sum_df: data frame con la sumatoria
    """
    # Nombre de las columnas por los robots que se tienen
    name_list = [name + " por " + i for i in df["Robot"].unique()]

    colum_name = df.columns.values.tolist()[2:]

    sum_df = pd.DataFrame(
        '',
        index=range(int(df[column].nunique())),
        columns=[column] + name_list)

    for i, elem in enumerate(df[column].unique()):
        sum_df.loc[sum_df.index[i], column] = elem
        for j, rob in enumerate(df["Robot"].unique()):
            sum_df.loc[sum_df.index[i], name_list[j]] = df[(df[column] == elem) &
                                                           (df["Robot"] == rob)][colum_name].sum().sum()

    return sum_df


def visual_tabla_dinam(df, key, flag_fecha=1):
    """
    Función para generar las tablas dinamicas que se visualizan
    INPUT:
        df: data frame a visualizar
        key: Llave distinta para el objeto de streamlit

    """
    # Copy dataframe
    df_aux = df.copy()

    # Definiendo la tabla de visualización
    gb = GridOptionsBuilder.from_dataframe(df_aux)
    gb.configure_side_bar()

    if flag_fecha == 1:
        df_aux['Fecha'] = pd.to_datetime(df_aux['Fecha'], format='%Y-%m-%d', exact=False)
        df_aux['Fecha_planta'] = pd.to_datetime(df_aux['Fecha_planta'], format='%Y-%m-%d', exact=False)
        gb.configure_column("Fecha", type=["dateColumnFilter", "customDateTimeFormat"],
                            custom_format_string='yyyy-MM-dd', pivot=True)
        gb.configure_column("Fecha_planta", type=["dateColumnFilter", "customDateTimeFormat"],
                            custom_format_string='yyyy-MM-dd', pivot=True)
    elif flag_fecha == 0:
        df_aux['Fecha_planta'] = pd.to_datetime(df_aux['Fecha_planta'], format='%Y-%m-%d', exact=False)
        gb.configure_column("Fecha_planta", type=["dateColumnFilter", "customDateTimeFormat"],
                            custom_format_string='yyyy-MM-dd', pivot=True)
    elif flag_fecha == 2:
        gb.configure_column("Fecha_AñoMes_planta", type=["dateColumnFilter", "customDateTimeFormat"],
                            custom_format_string='yyyy-MM', pivot=True)
    elif flag_fecha == 3:
        df_aux['Fecha'] = pd.to_datetime(df_aux['Fecha'], format='%Y-%m-%d', exact=False)
        gb.configure_column("Fecha", type=["dateColumnFilter", "customDateTimeFormat"],
                            custom_format_string='yyyy-MM-dd', pivot=True)

    gb.configure_grid_options(domLayout='normal')
    gridoptions = gb.build()

    AgGrid(df_aux, editable=False, sortable=True, filter=True, resizable=True, height=400, width='50%', defaultWidth=3,
           theme="balham",  # "light", "dark", "blue", "material" # defaultWidth=3, fit_columns_on_grid_load=False,
           key=key, reload_data=True, gridOptions=gridoptions,
           enable_enterprise_modules=True)
    return


def round_np(x):
    """
    Función que redondea una cifra
    """
    return np.round(x, 3)


# @st.cache(persist=False, allow_output_mutation=True, suppress_st_warning=True, show_spinner=True, ttl=24*3600)
@st.experimental_memo(suppress_st_warning=True, show_spinner=True)
def find_analisis(df, sel_celula, robot, text_dia, redownload):
    """
    Función que busca y carga el archivo de datos analizados o en su lugar analiza la data.
    INPUT:
        df: dataframe que contiene la serie de tiempo que se debe analizar
        sel_celula: Celula de donde viene la información
        robot: Indicador del robot analizado en STR
        text_dia: Información en STR sobre la fecha o rango analizado
        redownload = Debe descargarse la data o buscar dentro de los archivos previamente descargados
    OUTPUT:
        analisis_df: dataframe con los datos
    """
    # Setting the folder where to search
    if text_dia[:4] == "from":
        directory = './Data/Analizadas/'
        filenames = os.listdir(directory)
    else:
        directory = './Data/Analizadas/' + text_dia[:-3] + '/'
        if not os.path.exists(directory):
            os.makedirs(directory)
        filenames = os.listdir(directory)

    # Creo el nombre del archivo a buscar
    filename = 'analisis_' + robot + '_' + text_dia + '.csv'

    # Celula 4 option
    if sel_celula == 'Célula 4':
        if filename in filenames and redownload is False:
            analisis_df = pd.read_csv(directory + filename)

            # Drop the columns peso_antes y peso_despues if exist.
            analisis_df = analisis_df.drop(['Peso_Antes [Kg]', 'Peso_Despues [kg]'], axis=1, errors="ignore")
        else:
            analisis_df = analitica_esmalte(df=df, table=robot, periodo=text_dia)

        # Rename the following references in columns
        dict_replace = {37: 9147, 38: 9311, 39: 9312}
        analisis_df["Referencia"].replace(dict_replace, inplace=True)

    # Celula 1 option
    elif sel_celula == 'Célula 1':
        if filename in filenames and redownload is False:
            analisis_df = pd.read_csv(directory + filename)
        else:
            analisis_df = analitica_esmalte_test(df=df, table=robot, periodo=text_dia)

    return analisis_df


def correcion_div_0(tiempo_variable, tiempo_sp_var):
    """
    Función que corrige el error que causa la división por 0 que se puede presentar cuando el tiempo de las variables
    es igual a 0.
    INPUT:
        tiempo_variable: tiempo de la variable
        tiempo_sp_var: tiempo del set point
    OUTPUT:
        tiempo_variable: tiempo de la variable diferente de 0
        tiempo_sp_var: tiempo del set point diferente de 0

    """
    if tiempo_variable == 0:
        tiempo_variable = 0.001
    if tiempo_sp_var == 0:
        tiempo_sp_var = 0.001

    return tiempo_variable, tiempo_sp_var


def analisis_variable(df, idx_variable, variable, flag_var, tiempo_var, total_var, max_var, aux):
    if df.iloc[idx_variable][variable] > 0 and flag_var is True:
        # Existen datos, cambio aux a 1
        aux = 1

        # Diferencia en el tiempo
        if idx_variable > 0:
            diferencia_dato = df.index[idx_variable] - df.index[idx_variable - 1]

            # Acumulo la data del proceso
            tiempo_var += diferencia_dato.total_seconds()
            total_var += ((df.iloc[idx_variable][variable] + df.iloc[idx_variable - 1][variable]) / 2) \
                         * diferencia_dato.total_seconds()
        else:
            # Acumulo la data del proceso
            tiempo_var += 1
            total_var += df.iloc[idx_variable][variable]

        # Maximo de la variable
        if max_var < df.iloc[idx_variable][variable]:
            max_var = df.iloc[idx_variable][variable]

    # Método para identificar que el proceso finalizo
    elif df.iloc[idx_variable - 1][variable] > 0 and df.iloc[idx_variable][variable] == 0 and flag_var is True:
        # Evito error de desborde
        if idx_variable + 1 > df.shape[0] - 1:
            flag_var = False
        else:
            if df.iloc[idx_variable + 1][variable] == 0:
                flag_var = False

    return tiempo_var, total_var, max_var, flag_var, aux


@st.experimental_memo(suppress_st_warning=True, show_spinner=True)
def analitica_esmalte(df, table, periodo):
    """
    Programa que analiza la serie de tiempo y crea un df con data de cada proceso de esmaltado
    """
    # TODO1: El tiempo se debe contar como la diferencia del valor anterior y no considerar que siempre es 1 segundo.
    # Inicialización del DF
    analisis_df = pd.DataFrame(columns=["Fecha", "Dia", "Turno", "Hora", "Robot", "Proceso_Completo",
                                        "Referencia", "Tiempo_Estado [s]", "Tiempo_Esmaltado [s]",
                                        "Tiempo_Esmaltado_SP [s]",
                                        "Esmalte_Usado [Kg]", "Esmalte_Usado_SP [Kg]", "Diff_Esmalte [gr]",
                                        "Max_Fmasico [gr/min]",
                                        "Promedio_Fmasico [gr/min]", "Promedio_SP_Fmasico [gr/min]",
                                        "Desviacion_max_Fmasico [gr/min]",
                                        "Max_Presion_Red [psi]", "Min_Presion_Red [psi]", "Promedio_Presion_Red [psi]",
                                        "Max_Presion_Atomizacion [psi]", "Promedio_Presion_Atomizacion [psi]",
                                        "Promedio_SP_Presion_Atomizacion [psi]", "Desviacion_Presion_Atomizacion [psi]",
                                        "Max_Presion_Abanico [psi]", "Promedio_Presion_Abanico [psi]",
                                        "Promedio_SP_Presion_Abanico [psi]", "Desviacion_Presion_Abanico [psi]",
                                        "Fecha_planta"])

    # Inicialización de variables
    count = 0
    idx = 0

    # Mensaje de control
    print("Inicio proceso de analisis de la información")

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

        # Flujo masico
        flujo_masico_total = 0
        max_flujo_masico = 0
        aux_fm = 0
        aux_sfm = 0

        sp_flujo_masico_total = 0
        max_sp_fmasico = 0

        # Presión de red
        max_pred = 0
        total_pred = 0

        # Presiones
        total_pabanico = 0
        total_sp_pabanico = 0
        total_patomizacion = 0
        total_sp_patomizacion = 0

        aux_pat = 0
        aux_spat = 0
        aux_pab = 0
        aux_spab = 0

        max_patomizacion = 0
        max_sp_patomizacion = 0
        max_pabanico = 0
        max_sp_pabanico = 0

        #  Flag de control de entradas y ciclos
        flag_comp = 1
        flag_fmasico = True
        flag_sp_fmasico = True

        flag_patomizacion = True
        flag_sp_patomizacion = True
        flag_pabanico = True
        flag_sp_pabanico = True

        total_flag = True
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
            turno = np.floor(((df.index[idx] + datetime.timedelta(minutes=30))
                              - datetime.timedelta(hours=6)).time().hour / 8) + 1

            # Inicializar Presion de referencia minima
            min_pred = df.iloc[idx]["presion_red"]

            # Mensajes de control
            print(robot, fecha_proceso, hora)
            # --------------------------------------------------------------------------------------------
            # Recorro el proceso mientras el estado sea activo
            while df.iloc[idx]['estado'] == 1:
                # Cuento el tiempo que estado permanecio on
                # Diferencia en el tiempo
                if idx > 0:
                    # Acumulo la data del proceso
                    diferencia_tiempo = df.index[idx] - df.index[idx - 1]
                    tiempo_estado += diferencia_tiempo.total_seconds()

                    total_pred += ((df.iloc[idx]["presion_red"] + df.iloc[idx - 1]["presion_red"]) / 2) \
                                 * diferencia_tiempo.total_seconds()
                else:
                    # Acumulo la data del proceso
                    tiempo_estado += 1

                    total_pred += df.iloc[idx]["presion_red"]
                # --------------------------------------------------------------------------------------------
                # Calcular LA PRESION DE RED
                if max_pred < df.iloc[idx]["presion_red"]:
                    max_pred = df.iloc[idx]["presion_red"]

                if min_pred > df.iloc[idx]["presion_red"]:
                    min_pred = df.iloc[idx]["presion_red"]
                # --------------------------------------------------------------------------------------------
                idx_var = idx
                while total_flag is True:
                    # --------------------------------------------------------------------------------------------
                    # Conteo del flujo masico
                    tiempo_fmasico, flujo_masico_total, max_flujo_masico, flag_fmasico, aux_fm = analisis_variable(
                        df, idx_var, "fmasico", flag_fmasico, tiempo_fmasico, flujo_masico_total,
                        max_flujo_masico, aux_fm)
                    # --------------------------------------------------------------------------------------------
                    # Conteo del Set point flujo masico
                    tiempo_sp_fmasico, sp_flujo_masico_total, max_sp_fmasico, flag_sp_fmasico, \
                    aux_sfm = analisis_variable(df, idx_var, "sp_fmasico", flag_sp_fmasico, tiempo_sp_fmasico,
                                                sp_flujo_masico_total, max_sp_fmasico, aux_sfm)
                    # --------------------------------------------------------------------------------------------
                    # Conteo del Presion Atomizacion
                    tiempo_patomizacion, total_patomizacion, max_patomizacion, flag_patomizacion, \
                    aux_pat = analisis_variable(df, idx_var, "patomizacion", flag_patomizacion, tiempo_patomizacion,
                                                total_patomizacion, max_patomizacion, aux_pat)
                    # --------------------------------------------------------------------------------------------
                    # Conteo del  set_point -Presion Atomizacion
                    tiempo_sp_patomizacion, total_sp_patomizacion, max_sp_patomizacion, \
                    flag_sp_patomizacion, aux_spat = analisis_variable(df, idx_var, "sp_patomizacion",
                                                                       flag_sp_patomizacion, tiempo_sp_patomizacion,
                                                                       total_sp_patomizacion, max_sp_patomizacion,
                                                                       aux_spat)
                    # --------------------------------------------------------------------------------------------
                    # Conteo del Presion abanico
                    tiempo_pabanico, total_pabanico, max_pabanico, flag_pabanico, \
                    aux_pab = analisis_variable(df, idx_var, "pabanico", flag_pabanico, tiempo_pabanico,
                                                total_pabanico, max_pabanico, aux_pab)
                    # --------------------------------------------------------------------------------------------
                    # Conteo del  set_point -Presion abanico
                    tiempo_sp_pabanico, total_sp_pabanico, max_sp_pabanico, flag_sp_pabanico, \
                    aux_spab = analisis_variable(df, idx_var, "sp_pabanico", flag_sp_pabanico, tiempo_sp_pabanico,
                                                 total_sp_pabanico, max_sp_pabanico, aux_spab)
                    # --------------------------------------------------------------------------------------------
                    # --------------------------------------------------------------------------------------------
                    # Por si nunca empiezan los procesos durante el tiempo de estado on
                    if df.iloc[idx_var]['estado'] == 0:
                        if aux_fm == 0:
                            flag_fmasico = False
                        if aux_sfm == 0:
                            flag_sp_fmasico = False
                        if aux_pat == 0:
                            flag_patomizacion = False
                        if aux_spat == 0:
                            flag_sp_patomizacion = False
                        if aux_pab == 0:
                            flag_pabanico = False
                        if aux_spab == 0:
                            flag_sp_pabanico = False

                    # Logica para salir del while
                    if flag_fmasico is False and flag_sp_fmasico is False and flag_patomizacion is False and \
                            flag_sp_patomizacion is False and flag_pabanico is False and flag_sp_pabanico is False:
                        total_flag = False
                    elif idx_var == df.shape[0] - 1:
                        total_flag = False

                    idx_var += 1
                # --------------------------------------------------------------------------------------------
                # Avanzo en el df
                idx += 1

                # Por si el df finaliza o inicia con el estado 1, es decir que se corto el proceso
                if idx >= df.shape[0]:
                    flag_comp = 0
                    print("¡NO SE TIENEN DATOS SUFICIENTE DE LA ULTIMA PIEZA ESMALTADA: "
                          "El proceso no ha finalizado!\n")
                    break  # Salir del ciclo para evitar un error
                elif idx - 1 == 0:
                    flag_comp = -1
                    print("¡NO SE TIENEN DATOS SUFICIENTE DE LA PRIMERA PIEZA ESMALTADA: "
                          "El proceso no ha finalizado!\n")

            flujo_masico_total = flujo_masico_total / 60 / 1000
            sp_flujo_masico_total = sp_flujo_masico_total / 60 / 1000
            # ----------------------------------------------------------------------------------------------------------
            # Evitando la division por cero cuando el estado esta ON pero no sale flujo ni presión
            # ----------------------------------------------------------------------------------------------------------
            tiempo_fmasico, tiempo_sp_fmasico = correcion_div_0(tiempo_fmasico, tiempo_sp_fmasico)
            tiempo_patomizacion, tiempo_sp_patomizacion = correcion_div_0(tiempo_patomizacion, tiempo_sp_patomizacion)
            tiempo_pabanico, tiempo_sp_pabanico = correcion_div_0(tiempo_pabanico, tiempo_sp_pabanico)
            # -------------------------------------------------------------------------------------------------------------
            # Llenando los datos del DF analisis
            # -------------------------------------------------------------------------------------------------------------
            desv_flujo_masico_max = max_flujo_masico - (((sp_flujo_masico_total * 1000) / tiempo_sp_fmasico) * 60)

            analisis_df.loc[count] = [fecha_ini, ndia, turno, hora, robot, float(flag_comp),
                                      referencia_esmaltada, float(tiempo_estado),
                                      float(tiempo_fmasico), float(tiempo_sp_fmasico),
                                      round_np(flujo_masico_total), round_np(sp_flujo_masico_total),
                                      round_np((flujo_masico_total - sp_flujo_masico_total) * 1000),
                                      round_np(max_flujo_masico),
                                      round_np(((flujo_masico_total * 1000) / tiempo_fmasico) * 60),
                                      round_np(((sp_flujo_masico_total * 1000) / tiempo_sp_fmasico) * 60),  # [gr/min]
                                      round_np(desv_flujo_masico_max),
                                      max_pred, min_pred, round_np((total_pred / tiempo_estado)),
                                      max_patomizacion, round_np((total_patomizacion / tiempo_patomizacion)),
                                      round_np((total_sp_patomizacion / tiempo_sp_patomizacion)),
                                      round_np((total_patomizacion / tiempo_patomizacion) - (
                                              total_sp_patomizacion / tiempo_sp_patomizacion)),
                                      max_pabanico, round_np((total_pabanico / tiempo_pabanico)),
                                      round_np((total_sp_pabanico / tiempo_sp_pabanico)),
                                      round_np((total_pabanico / tiempo_pabanico) - (
                                              total_sp_pabanico / tiempo_sp_pabanico)),
                                      fecha_proceso]

            # Cuento la referencia esmaltada
            count += 1

        else:
            # Avanzo en el df
            idx += 1

    # Mensajes de control
    print("Finalizo correctamente")

    # Aseguro los datos como numericos
    float_columns = analisis_df.columns.values.tolist()[7:30]
    analisis_df[float_columns] = analisis_df[float_columns].apply(pd.to_numeric, errors='ignore')

    # Guardo el analisis realizado
    if periodo == str(datetime.date.today()):
        pass  # No guardar datos si el día seleccionado es el día actual del sistema
    else:
        # Checking and creating the folder
        if periodo[:4] == "from":
            analisis_df.to_csv('./Data/Analizadas/analisis_' + table + '_' + periodo + '.csv', index=False)
        else:
            folder = periodo[:-3]
            if not os.path.exists('./Data/Analizadas/' + folder):
                os.makedirs('./Data/Analizadas/' + folder)
            # Salvando el analisis
            analisis_df.to_csv('./Data/Analizadas/' + folder + '/analisis_' + table + '_' + periodo + '.csv',
                               index=False)

    return analisis_df


# TODO: Eliminar esta función, cuando se corrija lo del 0 en el flujo masico de la celula 1
def analisis_variable_masico_cel1(df, idx_variable, variable, flag_var, tiempo_var, total_var, max_var, aux):
    if df.iloc[idx_variable][variable] > 2 and flag_var is True:
        # Existen datos, cambio aux a 1
        aux = 1

        # Diferencia en el tiempo
        if idx_variable > 0:
            diferencia_dato = df.index[idx_variable] - df.index[idx_variable - 1]

            # Acumulo la data del proceso
            tiempo_var += diferencia_dato.total_seconds()
            total_var += ((df.iloc[idx_variable][variable] + df.iloc[idx_variable - 1][variable]) / 2) \
                         * diferencia_dato.total_seconds()
        else:
            # Acumulo la data del proceso
            tiempo_var += 1
            total_var += df.iloc[idx_variable][variable]

        # Maximo de la variable
        if max_var < df.iloc[idx_variable][variable]:
            max_var = df.iloc[idx_variable][variable]

    # Método para identificar que el proceso finalizo
    elif df.iloc[idx_variable - 1][variable] > 2 and df.iloc[idx_variable][variable] <= 2 and flag_var is True:
        # Evito error de desborde
        if idx_variable + 1 > df.shape[0] - 1:
            flag_var = False
        else:
            if df.iloc[idx_variable + 1][variable] <= 2:
                flag_var = False

    # print(f'{variable}: {flag_var}')

    return tiempo_var, total_var, max_var, flag_var, aux


# TODO: Eliminar esta función, cuando se corrija lo del 0 en el flujo masico de la celula 1
@st.experimental_memo(suppress_st_warning=True, show_spinner=True)
def analitica_esmalte_test(df, table, periodo):
    """
    Programa que analiza la serie de tiempo y crea un df con data de cada proceso de esmaltado
    """
    # TODO1: El tiempo se debe contar como la diferencia del valor anterior y no considerar que siempre es 1 segundo.
    # Inicialización del DF
    analisis_df = pd.DataFrame(columns=["Fecha", "Dia", "Turno", "Hora", "Robot", "Proceso_Completo",
                                        "Referencia", "Tiempo_Estado [s]", "Tiempo_Esmaltado [s]",
                                        "Tiempo_Esmaltado_SP [s]",
                                        "Esmalte_Usado [Kg]", "Esmalte_Usado_SP [Kg]", "Diff_Esmalte [gr]",
                                        "Max_Fmasico [gr/min]",
                                        "Promedio_Fmasico [gr/min]", "Promedio_SP_Fmasico [gr/min]",
                                        "Desviacion_max_Fmasico [gr/min]",
                                        "Max_Presion_Red [psi]", "Min_Presion_Red [psi]", "Promedio_Presion_Red [psi]",
                                        "Max_Presion_Atomizacion [psi]", "Promedio_Presion_Atomizacion [psi]",
                                        "Promedio_SP_Presion_Atomizacion [psi]", "Desviacion_Presion_Atomizacion [psi]",
                                        "Max_Presion_Abanico [psi]", "Promedio_Presion_Abanico [psi]",
                                        "Promedio_SP_Presion_Abanico [psi]", "Desviacion_Presion_Abanico [psi]",
                                        "Fecha_planta"])

    # Inicialización de variables
    count = 0
    idx = 0

    # Mensaje de control
    print("Inicio proceso de analisis de la información")
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

        # Flujo masico
        flujo_masico_total = 0
        max_flujo_masico = 0
        aux_fm = 0
        aux_sfm = 0

        sp_flujo_masico_total = 0
        max_sp_fmasico = 0

        # Presión de red
        max_pred = 0
        total_pred = 0

        # Presiones
        total_pabanico = 0
        total_sp_pabanico = 0
        total_patomizacion = 0
        total_sp_patomizacion = 0

        aux_pat = 0
        aux_spat = 0
        aux_pab = 0
        aux_spab = 0

        max_patomizacion = 0
        max_sp_patomizacion = 0
        max_pabanico = 0
        max_sp_pabanico = 0

        #  Flag de control de entradas y ciclos
        flag_comp = 1
        flag_fmasico = True
        flag_sp_fmasico = True

        flag_patomizacion = True
        flag_sp_patomizacion = True
        flag_pabanico = True
        flag_sp_pabanico = True

        total_flag = True
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
            turno = np.floor(((df.index[idx] + datetime.timedelta(minutes=30))
                              - datetime.timedelta(hours=6)).time().hour / 8) + 1

            # Inicializar Presion de referencia minima
            min_pred = df.iloc[idx]["presion_red"]

            # Mensajes de control
            print(robot, fecha_proceso, hora)
            # --------------------------------------------------------------------------------------------
            # Recorro el proceso mientras el estado sea activo
            while df.iloc[idx]['estado'] == 1:
                # Cuento el tiempo que estado permanece on
                # Diferencia en el tiempo
                if idx > 0:
                    # Acumulo la data del proceso
                    diferencia_tiempo = df.index[idx] - df.index[idx - 1]
                    tiempo_estado += diferencia_tiempo.total_seconds()

                    total_pred += ((df.iloc[idx]["presion_red"] + df.iloc[idx - 1]["presion_red"]) / 2) \
                                 * diferencia_tiempo.total_seconds()
                else:
                    # Acumulo la data del proceso
                    tiempo_estado += 1

                    total_pred += df.iloc[idx]["presion_red"]
                # --------------------------------------------------------------------------------------------
                # Calcular LA PRESION DE RED
                if max_pred < df.iloc[idx]["presion_red"]:
                    max_pred = df.iloc[idx]["presion_red"]

                if min_pred > df.iloc[idx]["presion_red"]:
                    min_pred = df.iloc[idx]["presion_red"]
                # --------------------------------------------------------------------------------------------
                idx_var = idx
                while total_flag is True:
                    # --------------------------------------------------------------------------------------------
                    # Conteo del flujo masico
                    tiempo_fmasico, flujo_masico_total, max_flujo_masico, flag_fmasico, aux_fm = analisis_variable_masico_cel1(
                        df, idx_var, "fmasico", flag_fmasico, tiempo_fmasico, flujo_masico_total,
                        max_flujo_masico, aux_fm)
                    # --------------------------------------------------------------------------------------------
                    # Conteo del Set point flujo masico
                    tiempo_sp_fmasico, sp_flujo_masico_total, max_sp_fmasico, flag_sp_fmasico, \
                    aux_sfm = analisis_variable(df, idx_var, "sp_fmasico", flag_sp_fmasico, tiempo_sp_fmasico,
                                                sp_flujo_masico_total, max_sp_fmasico, aux_sfm)
                    # --------------------------------------------------------------------------------------------
                    # Conteo del Presion Atomizacion
                    tiempo_patomizacion, total_patomizacion, max_patomizacion, flag_patomizacion, \
                    aux_pat = analisis_variable(df, idx_var, "patomizacion", flag_patomizacion, tiempo_patomizacion,
                                                total_patomizacion, max_patomizacion, aux_pat)
                    # --------------------------------------------------------------------------------------------
                    # Conteo del  set_point -Presion Atomizacion
                    tiempo_sp_patomizacion, total_sp_patomizacion, max_sp_patomizacion, \
                    flag_sp_patomizacion, aux_spat = analisis_variable(df, idx_var, "sp_patomizacion",
                                                                       flag_sp_patomizacion, tiempo_sp_patomizacion,
                                                                       total_sp_patomizacion, max_sp_patomizacion,
                                                                       aux_spat)
                    # --------------------------------------------------------------------------------------------
                    # Conteo del Presion abanico
                    tiempo_pabanico, total_pabanico, max_pabanico, flag_pabanico, \
                    aux_pab = analisis_variable(df, idx_var, "pabanico", flag_pabanico, tiempo_pabanico,
                                                total_pabanico, max_pabanico, aux_pab)
                    # --------------------------------------------------------------------------------------------
                    # Conteo del  set_point -Presion abanico
                    tiempo_sp_pabanico, total_sp_pabanico, max_sp_pabanico, flag_sp_pabanico, \
                    aux_spab = analisis_variable(df, idx_var, "sp_pabanico", flag_sp_pabanico, tiempo_sp_pabanico,
                                                 total_sp_pabanico, max_sp_pabanico, aux_spab)
                    # --------------------------------------------------------------------------------------------
                    # --------------------------------------------------------------------------------------------
                    # Por si nunca empiezan los procesos durante el tiempo de estado on
                    if df.iloc[idx_var]['estado'] == 0:
                        if aux_fm == 0:
                            flag_fmasico = False
                        if aux_sfm == 0:
                            flag_sp_fmasico = False
                        if aux_pat == 0:
                            flag_patomizacion = False
                        if aux_spat == 0:
                            flag_sp_patomizacion = False
                        if aux_pab == 0:
                            flag_pabanico = False
                        if aux_spab == 0:
                            flag_sp_pabanico = False

                    # Logica para salir del while
                    if flag_fmasico is False and flag_sp_fmasico is False and flag_patomizacion is False and \
                            flag_sp_patomizacion is False and flag_pabanico is False and flag_sp_pabanico is False:
                        total_flag = False
                    elif idx_var == df.shape[0] - 1:
                        total_flag = False

                    idx_var += 1
                # --------------------------------------------------------------------------------------------
                # Avanzo en el df
                idx += 1

                # Por si el df finaliza o inicia con el estado 1, es decir que se corto el proceso
                if idx >= df.shape[0]:
                    flag_comp = 0
                    print("¡NO SE TIENEN DATOS SUFICIENTE DE LA ULTIMA PIEZA ESMALTADA: "
                          "El proceso no ha finalizado!\n")
                    break  # Salir del ciclo para evitar un error
                elif idx - 1 == 0:
                    flag_comp = -1
                    print("¡NO SE TIENEN DATOS SUFICIENTE DE LA PRIMERA PIEZA ESMALTADA: "
                          "El proceso no ha finalizado!\n")

            flujo_masico_total = flujo_masico_total / 60 / 1000
            sp_flujo_masico_total = sp_flujo_masico_total / 60 / 1000
            # ----------------------------------------------------------------------------------------------------------
            # Evitando la division por cero cuando el estado esta ON pero no sale flujo ni presión
            # ----------------------------------------------------------------------------------------------------------
            tiempo_fmasico, tiempo_sp_fmasico = correcion_div_0(tiempo_fmasico, tiempo_sp_fmasico)
            tiempo_patomizacion, tiempo_sp_patomizacion = correcion_div_0(tiempo_patomizacion, tiempo_sp_patomizacion)
            tiempo_pabanico, tiempo_sp_pabanico = correcion_div_0(tiempo_pabanico, tiempo_sp_pabanico)
            # -------------------------------------------------------------------------------------------------------------
            # Llenando los datos del DF analisis
            # -------------------------------------------------------------------------------------------------------------
            desv_flujo_masico_max = max_flujo_masico - (((sp_flujo_masico_total * 1000) / tiempo_sp_fmasico) * 60)

            analisis_df.loc[count] = [fecha_ini, ndia, turno, hora, robot, float(flag_comp),
                                      referencia_esmaltada, float(tiempo_estado),
                                      float(tiempo_fmasico), float(tiempo_sp_fmasico),
                                      round_np(flujo_masico_total), round_np(sp_flujo_masico_total),
                                      round_np((flujo_masico_total - sp_flujo_masico_total) * 1000),
                                      round_np(max_flujo_masico),
                                      round_np(((flujo_masico_total * 1000) / tiempo_fmasico) * 60),
                                      round_np(((sp_flujo_masico_total * 1000) / tiempo_sp_fmasico) * 60),  # [gr/min]
                                      round_np(desv_flujo_masico_max),
                                      max_pred, min_pred, round_np((total_pred / tiempo_estado)),
                                      max_patomizacion, round_np((total_patomizacion / tiempo_patomizacion)),
                                      round_np((total_sp_patomizacion / tiempo_sp_patomizacion)),
                                      round_np((total_patomizacion / tiempo_patomizacion) - (
                                              total_sp_patomizacion / tiempo_sp_patomizacion)),
                                      max_pabanico, round_np((total_pabanico / tiempo_pabanico)),
                                      round_np((total_sp_pabanico / tiempo_sp_pabanico)),
                                      round_np((total_pabanico / tiempo_pabanico) - (
                                              total_sp_pabanico / tiempo_sp_pabanico)),
                                      fecha_proceso]

            # Cuento la referencia esmaltada
            count += 1

        else:
            # Avanzo en el df
            idx += 1

    # Mensajes de control
    print("Finalizo correctamente")

    # Aseguro los datos como numericos
    float_columns = analisis_df.columns.values.tolist()[7:30]
    analisis_df[float_columns] = analisis_df[float_columns].apply(pd.to_numeric, errors='ignore')

    # Guardo el analisis realizado
    if periodo == str(datetime.date.today()):
        pass  # No guardar datos si el día seleccionado es el día actual del sistema
    else:
        # Checking and creating the folder
        if periodo[:4] == "from":
            analisis_df.to_csv('./Data/Analizadas/analisis_' + table + '_' + periodo + '.csv', index=False)
        else:
            folder = periodo[:-3]
            if not os.path.exists('./Data/Analizadas/' + folder):
                os.makedirs('./Data/Analizadas/' + folder)
            # Salvando el analisis
            analisis_df.to_csv('./Data/Analizadas/' + folder + '/analisis_' + table + '_' + periodo + '.csv',
                               index=False)

    return analisis_df
