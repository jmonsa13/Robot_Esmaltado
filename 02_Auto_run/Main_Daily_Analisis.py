# Python File for analysing the data
# GUI APP for IIOT | Corona
# 19-January-2022
# ----------------------------------------------------------------------------------------------------------------------
# Libraries
import datetime

from SQL_Function_AR import get_data_day
from Analysis_Function_AR import find_analisis
# ----------------------------------------------------------------------------------------------------------------------
# Setting the condition for the analisis
robots = "Ambos"
ayer = datetime.date.today() - datetime.timedelta(days=1)
flag_download = True

# ----------------------------------------------------------------------------------------------------------------------
# Getting the data
print("Se descargara el día {}".format(ayer))
df, df2, salud_list, salud_datos, title = get_data_day(robots, ayer, flag_download)
text_dia = str(ayer)

# ----------------------------------------------------------------------------------------------------------------------
# Analysing the data
print("Se analizara el día {}".format(ayer))
Analisis_df1 = find_analisis(df=df, robot="robot1", text_dia=text_dia, redownload=flag_download)
Analisis_df2 = find_analisis(df=df2, robot="robot2", text_dia=text_dia, redownload=flag_download)
# Analisis_df = pd.concat([Analisis_df1, Analisis_df2])
