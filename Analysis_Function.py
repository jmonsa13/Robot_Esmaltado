# Python File function for streamlit tools
# Analysis function for IIOT | Colceramica
# 21-September-2021
# ----------------------------------------------------------------------------------------------------------------------
# Libraries
import datetime

import numpy as np
import pandas as pd
import streamlit as st

from st_aggrid import AgGrid, GridOptionsBuilder
# ----------------------------------------------------------------------------------------------------------------------
# Function definition


def visual_tabla_dinam(df, key):
    # Definiendo la tabla de visualización
    gb = GridOptionsBuilder.from_dataframe(df)

    gb.configure_side_bar()
    gridoptions = gb.build()

    AgGrid(df, editable=False, sortable=True, filter=True, resizable=True, defaultWidth=5,
           fit_columns_on_grid_load=False, theme="streamlit",  # "light", "dark", "blue", "material"
           key=key, reload_data=True,
           gridOptions=gridoptions, enable_enterprise_modules=True)
    return


@st.cache(persist=False, allow_output_mutation=True, suppress_st_warning=True, show_spinner=True)
def round_np(x):
    """
    Función que redondea una cifra
    """
    return np.round(x, 3)


@st.cache(persist=False, allow_output_mutation=True, suppress_st_warning=True, show_spinner=True)
def analitica_esmalte(df):
    """
    Programa que analisa la serie de tiempo y crea un df con data de cada proceso de esmaltado
    """
    # Inicialización del DF
    Analisis_df = pd.DataFrame(columns=["Fecha", "Día", "Turno", "Hora", "Robot", "Proceso_Completo",
                                        "Referencia", "Tiempo_Estado [s]", "Tiempo_Esmaltado [s]",
                                        "Tiempo_Esmaltado_SP [s]",
                                        "Esmalte_Usado [Kg]", "Esmalte_Usado_SP [Kg]", "Diff_Esmalte [gr]",
                                        "Max_Fmasico [gr/min]",
                                        "Promedio_Fmasico [gr/min]", "Promedio_SP_Fmasico [gr/min]",
                                        "Desviación_max_Fmasico [gr/min]", "Peso_Antes [Kg]", "Peso_Despues [kg]",
                                        "Max_Presión_Red [psi]", "Min_Presión_Red [psi]", "Promedio_Presión_Red [psi]",
                                        "Max_Presión_Atomización [psi]", "Promedio_Presión_Atomización [psi]",
                                        "Promedio_SP_Presión_Atomización [psi]", "Desviación_Presión_Atomización [psi]",
                                        "Max_Presión_Abanico [psi]", "Promedio_Presión_Abanico [psi]",
                                        "Promedio_SP_Presión_Abanico [psi]", "Desviación_Presión_Abanico [psi]",
                                        "Fecha_planta"])

    # Inicialización de variables
    count = 0
    idx = 0
    pre = 3

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

        # Flujo masico y set point flujo masico y desviacion flujo masico
        flujo_masico_total = 0
        max_flujo_masico = 0
        sp_flujo_masico_total = 0
        desv_flujo_masico_max = 0

        # Presion de red
        Max_Pred = 0
        Min = 0
        Total_Pred = 0

        # Presion Atomización
        total_patomizacion = 0
        max_patomizacion = 0
        total_sp_patomizacion = 0

        # Presion Abanico
        total_pabanico = 0
        max_pabanico = 0
        total_sp_pabanico = 0

        #  Flag de control de entradas y ciclos
        flag_comp = 1
        flag_fmasico = True
        flag_sp_fmasico = True

        flag_patomizacion = True
        flag_sp_patomizacion = True
        flag_pabanico = True
        flag_sp_pabanico = True
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
            turno = np.floor((df.index[idx] - datetime.timedelta(hours=6)).time().hour / 8) + 1

            # Guardo el peso antes y peso despues OJO AQUI HAY UN ERROR
            peso_antes = df.iloc[idx]["peso_antes"]
            peso_despues = df.iloc[idx]["peso_despues"]

            # Inicializar Presion de referencia minima
            Min_Pred = df.iloc[idx]["presion_red"]

            # --------------------------------------------------------------------------------------------
            # Recorro el proceso mientras el estado sea activo
            while df.iloc[idx]['estado'] == 1:
                # Cuento el tiempo que estado permanecio on
                tiempo_estado += 1

                # --------------------------------------------------------------------------------------------
                # Calcular LA PRESION DE RED
                if Max_Pred < df.iloc[idx]["presion_red"]:
                    Max_Pred = df.iloc[idx]["presion_red"]

                if Min_Pred > df.iloc[idx]["presion_red"]:
                    Min_Pred = df.iloc[idx]["presion_red"]

                Total_Pred += df.iloc[idx]["presion_red"]

                # --------------------------------------------------------------------------------------------
                # Calcular la desviación del flujo masico vs la del set point
                # desv_flujo_masico_aux = abs((df.iloc[idx]["fmasico"] - df.iloc[idx]["sp_fmasico"])/60)
                #
                # if desv_flujo_masico_aux > abs(desv_flujo_masico_max):
                #    desv_flujo_masico_max = (df.iloc[idx]["fmasico"] - df.iloc[idx]["sp_fmasico"])/60

                # --------------------------------------------------------------------------------------------
                # Conteo del flujo masico
                if df.iloc[idx]['fmasico'] > 0 and flag_fmasico is True:
                    idx_fmasico = idx

                    while df.iloc[idx_fmasico]['fmasico'] > 0 or df.iloc[idx_fmasico + 1]['fmasico'] > 0:

                        # Acumulo la data del proceso
                        tiempo_fmasico += 1
                        flujo_masico_total += df.iloc[idx_fmasico]["fmasico"] / 60 / 1000

                        # Maximo del flujo maxico
                        if max_flujo_masico < df.iloc[idx_fmasico]["fmasico"]:
                            max_flujo_masico = df.iloc[idx_fmasico]["fmasico"]

                        # Avanzo en el df
                        idx_fmasico += 1

                        # Por si el df finaliza o inicia con el estado 1, es decir que se corto el proceso
                        if idx_fmasico >= df.shape[0]:
                            flag_comp = 0
                            print(
                                "¡NO SE TIENEN DATOS SUFICIENTE DE LA ULTIMA PIEZA ESMALTADA: "
                                "El proceso no ha finalizado!\n")
                            break  # Salir del ciclo para evitar un error
                        elif idx_fmasico - 1 == 0:
                            flag_comp = 0
                            print(
                                "¡NO SE TIENEN DATOS SUFICIENTE DE LA PRIMERA PIEZA ESMALTADA: "
                                "El proceso no ha finalizado!\n")

                    # Flag para no volver a entrar
                    flag_fmasico = False

                # --------------------------------------------------------------------------------------------
                # Conteo del Set point flujo masico
                if df.iloc[idx]['sp_fmasico'] > 0 and flag_sp_fmasico is True:
                    idx_fmasico = idx

                    while df.iloc[idx_fmasico]['sp_fmasico'] > 0 or df.iloc[idx_fmasico + 1]['sp_fmasico'] > 0:

                        # Acumulo la data del proceso
                        tiempo_sp_fmasico += 1
                        sp_flujo_masico_total += df.iloc[idx_fmasico]["sp_fmasico"] / 60 / 1000

                        # Avanzo en el df
                        idx_fmasico += 1

                        # Por si el df finaliza o inicia con el estado 1, es decir que se corto el proceso
                        if idx_fmasico >= df.shape[0]:
                            flag_comp = 0
                            break  # Salir del ciclo para evitar un error
                        elif idx_fmasico - 1 == 0:
                            flag_comp = 0

                    # Flag para no volver a entrar
                    flag_sp_fmasico = False

                # --------------------------------------------------------------------------------------------
                # Conteo del Presion Atomizacion
                if df.iloc[idx]['patomizacion'] > 0 and flag_patomizacion is True:
                    idx_fmasico = idx

                    while df.iloc[idx_fmasico]['patomizacion'] > 0 or df.iloc[idx_fmasico + 1]['patomizacion'] > 0:

                        # Acumulo la data del proceso
                        tiempo_patomizacion += 1
                        total_patomizacion += df.iloc[idx_fmasico]["patomizacion"]

                        # Maximo de la presion de atomizacion
                        if max_patomizacion < df.iloc[idx_fmasico]["patomizacion"]:
                            max_patomizacion = df.iloc[idx_fmasico]["patomizacion"]

                        # Avanzo en el df
                        idx_fmasico += 1

                        # Por si el df finaliza o inicia con el estado 1, es decir que se corto el proceso
                        if idx_fmasico >= df.shape[0]:
                            flag_comp = 0
                            break  # Salir del ciclo para evitar un error
                        elif idx_fmasico - 1 == 0:
                            flag_comp = 0

                    # Flag para no volver a entrar
                    flag_patomizacion = False
                # --------------------------------------------------------------------------------------------
                # Conteo del  set_point -Presion Atomizacion
                if df.iloc[idx]['sp_patomizacion'] > 0 and flag_sp_patomizacion is True:
                    idx_fmasico = idx

                    while df.iloc[idx_fmasico]['sp_patomizacion'] > 0 or df.iloc[idx_fmasico + 1]['sp_patomizacion'] > 0:

                        # Acumulo la data del proceso
                        tiempo_sp_patomizacion += 1
                        total_sp_patomizacion += df.iloc[idx_fmasico]["sp_patomizacion"]

                        # Maximo de la presion de atomizacion
                        # if max_patomizacion < df.iloc[idx_fmasico]["sp_patomizacion"]:
                        #    max_patomizacion = df.iloc[idx_fmasico]["sp_patomizacion"]

                        # Avanzo en el df
                        idx_fmasico += 1

                        # Por si el df finaliza o inicia con el estado 1, es decir que se corto el proceso
                        if idx_fmasico >= df.shape[0]:
                            flag_comp = 0
                            break  # Salir del ciclo para evitar un error
                        elif idx_fmasico - 1 == 0:
                            flag_comp = 0

                    # Flag para no volver a entrar
                    flag_sp_patomizacion = False

                # --------------------------------------------------------------------------------------------
                # Conteo del Presion abanico
                if df.iloc[idx]['pabanico'] > 0 and flag_pabanico is True:
                    idx_fmasico = idx

                    while df.iloc[idx_fmasico]['pabanico'] > 0 or df.iloc[idx_fmasico + 1]['pabanico'] > 0:

                        # Acumulo la data del proceso
                        tiempo_pabanico += 1
                        total_pabanico += df.iloc[idx_fmasico]["pabanico"]

                        # Maximo de la presion de atomizacion
                        if max_pabanico < df.iloc[idx_fmasico]["pabanico"]:
                            max_pabanico = df.iloc[idx_fmasico]["pabanico"]

                        # Avanzo en el df
                        idx_fmasico += 1

                        # Por si el df finaliza o inicia con el estado 1, es decir que se corto el proceso
                        if idx_fmasico >= df.shape[0]:
                            flag_comp = 0
                            break  # Salir del ciclo para evitar un error
                        elif idx_fmasico - 1 == 0:
                            flag_comp = 0

                    # Flag para no volver a entrar
                    flag_pabanico = False
                # --------------------------------------------------------------------------------------------
                # Conteo del  set_point -Presion abanico
                if df.iloc[idx]['sp_pabanico'] > 0 and flag_sp_pabanico is True:
                    idx_fmasico = idx

                    while df.iloc[idx_fmasico]['sp_pabanico'] > 0 or df.iloc[idx_fmasico + 1]['sp_pabanico'] > 0:

                        # Acumulo la data del proceso
                        tiempo_sp_pabanico += 1
                        total_sp_pabanico += df.iloc[idx_fmasico]["sp_pabanico"]

                        # Maximo de la presion de atomizacion
                        # if max_patomizacion < df.iloc[idx_fmasico]["sp_pabanico"]:
                        #    max_patomizacion = df.iloc[idx_fmasico]["sp_pabanico"]

                        # Avanzo en el df
                        idx_fmasico += 1

                        # Por si el df finaliza o inicia con el estado 1, es decir que se corto el proceso
                        if idx_fmasico >= df.shape[0]:
                            flag_comp = 0
                            break  # Salir del ciclo para evitar un error
                        elif idx_fmasico - 1 == 0:
                            flag_comp = 0

                    # Flag para no volver a entrar
                    flag_sp_pabanico = False
                # --------------------------------------------------------------------------------------------
                # Avanzo en el df
                idx += 1

                # Por si el df finaliza o inicia con el estado 1, es decir que se corto el proceso
                if idx >= df.shape[0]:
                    flag_comp = 0
                    break  # Salir del ciclo para evitar un error
                elif idx - 1 == 0:
                    flag_comp = 0

            # ----------------------------------------------------------------------------------------------------------
            # Evitando la division por cero cuando el estado esta ON pero no sale flujo ni presión
            # ----------------------------------------------------------------------------------------------------------
            if tiempo_fmasico == 0:
                tiempo_fmasico = tiempo_sp_fmasico
                if tiempo_fmasico == 0:
                    tiempo_fmasico = 1
                    tiempo_sp_fmasico = 1
                # tiempo_fmasico = tiempo_estado
                print("Tiempo fmasico ", tiempo_fmasico)
                print(hora)

            if tiempo_patomizacion == 0:
                tiempo_patomizacion = tiempo_sp_patomizacion
                if tiempo_patomizacion == 0:
                    tiempo_patomizacion = 1
                    tiempo_sp_patomizacion = 1
                # tiempo_patomizacion = tiempo_estado
                print("Tiempo patomizacion ", tiempo_patomizacion)
                print(hora)

            if tiempo_pabanico == 0:
                tiempo_pabanico = tiempo_sp_pabanico
                if tiempo_pabanico == 0:
                    tiempo_pabanico = 1
                    tiempo_sp_pabanico = 1
                # tiempo_pabanico = tiempo_estado
                print("Tiempo pabanico ", tiempo_pabanico)
                print(hora)

            # -------------------------------------------------------------------------------------------------------------
            # Llenando los datos del DF analisis
            # -------------------------------------------------------------------------------------------------------------
            desv_flujo_masico_max = max_flujo_masico - (((sp_flujo_masico_total * 1000) / tiempo_sp_fmasico) * 60)

            Analisis_df.loc[count] = [fecha_ini, ndia, turno, hora, robot, float(flag_comp),
                                      referencia_esmaltada,float(tiempo_estado),
                                      float(tiempo_fmasico), float(tiempo_sp_fmasico),
                                      round_np(flujo_masico_total), round_np(sp_flujo_masico_total),
                                      round_np((flujo_masico_total - sp_flujo_masico_total)* 1000),
                                      round_np(max_flujo_masico),
                                      round_np(((flujo_masico_total * 1000) / tiempo_fmasico)*60),
                                      round_np(((sp_flujo_masico_total * 1000) / tiempo_sp_fmasico)*60), #[gr/min]
                                      round_np(desv_flujo_masico_max), peso_antes, peso_despues,
                                      Max_Pred, Min_Pred, round_np((Total_Pred/ tiempo_estado)),
                                      max_patomizacion, round_np((total_patomizacion/tiempo_patomizacion)),
                                      round_np((total_sp_patomizacion / tiempo_sp_patomizacion)),
                                      round_np((total_patomizacion/tiempo_patomizacion)-(total_sp_patomizacion/tiempo_sp_patomizacion)),
                                      max_pabanico, round_np((total_pabanico/tiempo_pabanico)),
                                      round_np((total_sp_pabanico/tiempo_sp_pabanico)),
                                      round_np((total_pabanico/tiempo_pabanico) - (total_sp_pabanico/tiempo_sp_pabanico)),
                                      fecha_proceso]

            # Cuento la referencia esmaltada
            count += 1

        else:
            # Avanzo en el df
            idx += 1

    #print("Se han esmaltado %i piezas" % count)

    return Analisis_df
