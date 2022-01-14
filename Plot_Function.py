# Python File function for streamlit tools
# Plot Function for IIOT | Colceramica
# 21-September-2021
# ----------------------------------------------------------------------------------------------------------------------
# Libraries
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots


# ----------------------------------------------------------------------------------------------------------------------
# Function definition
@st.cache(persist=False, allow_output_mutation=True, suppress_st_warning=True, show_spinner=True, ttl=24 * 3600)
def plot_total(df, salud, title, ytitle, fecha_column="Fecha_planta", flag=False, limit=700):
    """
    Función para dibujar las lines plot con los datos totales dia a dia de cada robot
    INPUT:
        df = pandas dataframe pivoteado.
        salud = lista con la salud de la data periodo a periodo
        title = Título de la gráfica
        ytitle = Título del eje y
        fecha_column= Nombre de la columna que contiene las fechas
        flag = Variable bandera para activar el límite de piezas esmaltadas
    OUTPUT:
        fig = objeto figura para dibujarlo externamente de la función
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Bar and line plot together
    for i in df.columns.values.tolist()[1:]:
        if i == "Total":
            fig.add_trace(go.Scatter(x=df[fecha_column],
                                     y=df["Total"],
                                     mode='markers',  # 'lines+markers'
                                     line=dict(color='gray', width=0.8),
                                     marker=dict(size=6),
                                     name=i.split(" ")[-1],
                                     showlegend=True))
        else:
            fig.add_trace(go.Bar(x=df[fecha_column],
                                 y=df[i],
                                 # text=df[int(elem)],textposition='auto',
                                 name=i.split(" ")[-1]))

    # Salud de los datos  en un line plot en un secundo eje
    fig.add_trace(go.Scatter(x=df[fecha_column],
                             y=salud,
                             line=dict(color='black', width=0.8),
                             mode='lines+markers',  # 'lines+markers'
                             marker=dict(size=6),
                             name="Salud_datos",
                             visible='legendonly'),
                  secondary_y=True)

    # Objetivo de fabricación
    if flag is True:
        fig.add_hline(y=limit, line_width=0.8, line_dash="dash", line_color="blue")
        fig.update_layout(yaxis_range=[0, 1000], barmode='group', bargap=0.3, bargroupgap=0.02, xaxis_tickangle=90)
    else:
        fig.update_layout(barmode='stack', bargap=0.3, bargroupgap=0.02, xaxis_tickangle=90)

    # Add figure title
    fig.update_layout(height=500, width=700, template="seaborn", title=title)
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0.01))
    fig.update_layout(modebar_add=["v1hovermode", "toggleSpikeLines"])

    # Set x-axis and y-axis title
    fig['layout']['xaxis']['title'] = 'Fecha'
    fig.update_xaxes(showline=True, linewidth=0.5, linecolor='black')
    fig.update_xaxes(dtick="d0.5", tickformat="%b %d\n%Y")

    fig.update_yaxes(showline=True, linewidth=0.5, linecolor='black')
    fig.update_yaxes(title_text=ytitle, secondary_y=False)
    fig.update_yaxes(title_text="Salud de los datos [%]", secondary_y=True)

    return fig


@st.cache(persist=False, allow_output_mutation=True, suppress_st_warning=True, show_spinner=True, ttl=24 * 3600)
def plot_bar_turno(df, salud, title, ytitle, fecha_column="Fecha_planta"):
    """
    Función para dibujar el bar plot con los datos de las tablas dinamicas
    INPUT:
        df = pandas dataframe pivoteado.
        salud = a List with the value of the health from the data
        title = Título de la grafica
        ytitle = Título del ejey
    OUTPUT:
        fig = objeto figura para dibujarlo externamente de la función
    """
    df["Turno"] = df["Turno"].astype(str)

    # fig = px.bar(df, x="Fecha_planta", y="Cantidad", color="Turno")

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    for i in df["Turno"].unique():
        aux = df[df["Turno"] == i]
        fig.add_trace(go.Bar(
            x=aux[fecha_column],
            y=aux["Cantidad"],
            # text=df[int(elem)],textposition='auto',
            name="Turno {}".format(i)))

    # Salud de los datos en un line plot
    fig.add_trace(go.Scatter(x=df[fecha_column].unique(),
                             y=salud,
                             line=dict(color='black', width=0.8),
                             mode='lines+markers',  # 'lines+markers'
                             marker=dict(size=6),
                             name="Salud_datos",
                             visible='legendonly'),
                  secondary_y=True)

    # Here we modify the tickangle of the xaxis, resulting in rotated labels.
    fig.update_layout(barmode='group', bargap=0.3, bargroupgap=0.02, xaxis_tickangle=90)
    fig.update_layout(height=500, width=700, template="seaborn", title=title)
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0.01))
    fig.update_layout(modebar_add=["v1hovermode", "toggleSpikeLines"])

    # Set x-axis and y-axis title
    fig['layout']['xaxis']['title'] = 'Fecha'

    fig.update_xaxes(showline=True, linewidth=0.5, linecolor='black')
    fig.update_yaxes(showline=True, linewidth=0.5, linecolor='black')
    fig.update_xaxes(dtick="d0.5", tickformat="%b %d\n%Y")
    fig.update_yaxes(title_text=ytitle, secondary_y=False)
    fig.update_yaxes(title_text="Salud de los datos [%]", secondary_y=True)

    return fig


@st.cache(persist=False, allow_output_mutation=True, suppress_st_warning=True, show_spinner=True, ttl=24 * 3600)
def plot_bar_referencia(df, salud, title, ytitle, fecha_column="Fecha_planta", flag=True):
    """
    Funcion para dibujar el bar plot con los datos de las tablas dinamicas
    INPUT:
        df = pandas dataframe pivoteado.
        title = Título de la grafica
        ytitle = Título del ejey
    OUTPUT:
        fig = objeto figura para dibujarlo externamente de la función
    """
    iter_colum = df.columns.values.tolist()[2:]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Bar group por referencia
    for elem in iter_colum:
        fig.add_trace(go.Bar(
            x=df[fecha_column],
            y=df[elem],
            # text=df[int(elem)],textposition='auto',
            name=elem))

    # Salud de los datos en un line plot
    fig.add_trace(go.Scatter(x=df[fecha_column].unique(),
                             y=salud,
                             line=dict(color='black', width=0.8),
                             mode='lines+markers',  # 'lines+markers'
                             marker=dict(size=6),
                             name="Salud_datos",
                             visible='legendonly'),
                  secondary_y=True)

    # Here we modify the tickangle of the xaxis, resulting in rotated labels.
    if flag is True:
        fig.update_layout(barmode='group', bargap=0.3, bargroupgap=0.02, xaxis_tickangle=90)
    else:
        fig.update_layout(barmode='stack', bargap=0.3, bargroupgap=0.02, xaxis_tickangle=90)

    fig.update_layout(height=500, width=700, legend=dict(orientation="v"), template="seaborn", title=title)
    fig.update_layout(modebar_add=["v1hovermode", "toggleSpikeLines"])

    # Set x-axis and y-axis title
    fig['layout']['xaxis']['title'] = 'Fecha'
    fig.update_xaxes(showline=True, linewidth=0.5, linecolor='black')
    fig.update_xaxes(dtick="d0.5", tickformat="%b %d\n%Y")

    fig.update_yaxes(showline=True, linewidth=0.5, linecolor='black')
    fig.update_yaxes(title_text=ytitle, secondary_y=False)
    fig.update_yaxes(title_text="Salud de los datos [%]", secondary_y=True)

    return fig


@st.cache(persist=False, allow_output_mutation=True, suppress_st_warning=True, show_spinner=True, ttl=24 * 3600)
def plot_html(df, title):
    """
    Funcion para dibujar los datos de un robot de esmaltado
    INPUT:
        df = pandas dataframe traído de la base de dato SQL del robot
        title = Título de la grafica
    OUTPUT:
        fig = objeto figura para dibujarlo externamente de la función
    """
    # Create figure with secondary y-axis
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.02,
                        # subplot_titles=('Flujo Masico',  'Presión Atomización')
                        )
    # ----------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------
    # Referencia
    fig.add_trace(go.Scatter(x=df.index, y=df["referencia"],
                             line=dict(color='black', width=1),
                             mode='lines',  # 'lines+markers'
                             name='Referencia'),
                  row=1, col=1)
    # ----------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------
    # SP_FMASICO
    fig.add_trace(go.Scatter(x=df.index, y=df["sp_fmasico"],
                             line=dict(color='darkorange', width=1, dash='dash'),
                             mode='lines',  # 'lines+markers'
                             name='sp_fmasico'),
                  row=2, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["fmasico"],
                             line=dict(color='steelblue', width=1),
                             mode='lines',  # 'lines+markers'
                             name='fmasico'), secondary_y=False,
                  row=2, col=1)
    # ----------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------
    # SP_PATOMIZACION
    fig.add_trace(go.Scatter(x=df.index, y=df["presion_red"],
                             line=dict(color='silver', width=1),
                             mode='lines', name='Presion Red', legendgroup="Presión red", showlegend=True),
                  secondary_y=False, row=3, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["sp_patomizacion"],
                             line=dict(color='orangered', width=1, dash='dash'),
                             mode='lines', name='sp_patomizacion'),
                  secondary_y=False, row=3, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["patomizacion"],
                             line=dict(color='olivedrab', width=1),
                             mode='lines', name='patomizacion'),
                  secondary_y=False, row=3, col=1)
    # ----------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------
    # SP_PABANICO
    fig.add_trace(go.Scatter(x=df.index, y=df["presion_red"],
                             line=dict(color='silver', width=1),
                             mode='lines', name='Presion Red', legendgroup="Presión red", showlegend=False),
                  secondary_y=False, row=4, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["sp_pabanico"],
                             line=dict(color='grey', width=1, dash='dash'),
                             mode='lines', name='sp_pabanico'),
                  secondary_y=False, row=4, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["pabanico"],
                             line=dict(color='teal', width=1),
                             mode='lines', name='pabanico'),
                  secondary_y=False, row=4, col=1)

    # Add figure title
    fig.update_layout(height=1000, title=title)

    # Template
    fig.layout.template = 'seaborn'  # ggplot2, plotly_dark, seaborn, plotly, plotly_white
    fig.update_layout(modebar_add=["v1hovermode", "toggleSpikeLines"])

    # Set x-axis and y-axis title
    # fig.update_xaxes(title = "xaxis title")
    # fig['layout']['xaxis']['title']='Tiempo'
    fig['layout']['xaxis4']['title'] = 'Fecha'
    fig['layout']['yaxis']['title'] = 'Referencia'
    fig['layout']['yaxis2']['title'] = 'Flujo Masico'
    fig['layout']['yaxis3']['title'] = 'P Atomización'
    fig['layout']['yaxis4']['title'] = 'P Abanico'
    fig.update_xaxes(showline=True, linewidth=0.5, linecolor='black')
    fig.update_yaxes(showline=True, linewidth=0.5, linecolor='black')

    # fig.show()

    return fig


@st.cache(persist=False, allow_output_mutation=True, suppress_st_warning=True, show_spinner=True, ttl=24 * 3600)
def plot_html_all(df, df2, title_plot):
    """
    Función para dibujar los 2 robots en 1 misma gráfica
    INPUT:
        df = Pandas dataframe traído de la base de dato SQL del robot 1
        df2 = Pandas dataframe traído de la base de dato SQL del robot 2
        title = Título de la gráfica
    OUTPUT:
        fig = Objeto figura para dibujarlo externamente de la función
    """
    # Create figure with secondary y-axis
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.02,
                        # subplot_titles=('Flujo Masico',  'Presión Atomización')
                        )

    # Referencia
    fig.add_trace(go.Scatter(x=df.index, y=df["referencia"],
                             line=dict(color='black', width=1),
                             mode='lines',  # 'lines+markers'
                             name='Referencia 1', legendgroup="Ref", showlegend=True),
                  row=1, col=1)
    # ----------------------------------------------------------------------------------------------------------
    fig.add_trace(go.Scatter(x=df.index, y=df2["referencia"],
                             line=dict(color='silver', width=1),
                             mode='lines',  # 'lines+markers'
                             name='Referencia 2', legendgroup="Ref2", showlegend=True),
                  row=1, col=1)
    # ----------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------
    # SP_FMASICO
    fig.add_trace(go.Scatter(x=df.index, y=df["sp_fmasico"],
                             line=dict(color='darkorange', width=1, dash='dash'),
                             mode='lines',  # 'lines+markers'
                             name='sp_fmasico 1', legendgroup="Ref", showlegend=True),
                  row=2, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["fmasico"],
                             line=dict(color='steelblue', width=1),
                             mode='lines',  # 'lines+markers'
                             name='fmasico 1', legendgroup="Ref", showlegend=True),
                  secondary_y=False, row=2, col=1)
    # ----------------------------------------------------------------------------------------------------------
    fig.add_trace(go.Scatter(x=df.index, y=df2["sp_fmasico"],
                             line=dict(color='grey', width=1, dash='dash'),
                             mode='lines',  # 'lines+markers'
                             name='sp_fmasico 2', legendgroup="Ref2", showlegend=True),
                  row=2, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df2["fmasico"],
                             line=dict(color='olivedrab', width=1),
                             mode='lines',  # 'lines+markers'
                             name='fmasico 2', legendgroup="Ref2", showlegend=True),
                  secondary_y=False, row=2, col=1)
    # ----------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------
    # SP_PATOMIZACION
    fig.add_trace(go.Scatter(x=df.index, y=df["presion_red"],
                             line=dict(color='black', width=1),
                             mode='lines', name='Presion Red 1', legendgroup="Ref", showlegend=True),
                  secondary_y=False, row=3, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["sp_patomizacion"],
                             line=dict(color='darkorange', width=1, dash='dash'),
                             mode='lines', name='sp_patomizacion 1', legendgroup="Ref", showlegend=True),
                  secondary_y=False, row=3, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["patomizacion"],
                             line=dict(color='steelblue', width=1),
                             mode='lines', name='patomizacion 1', legendgroup="Ref", showlegend=True),
                  secondary_y=False, row=3, col=1)

    # ----------------------------------------------------------------------------------------------------------
    fig.add_trace(go.Scatter(x=df.index, y=df2["presion_red"],
                             line=dict(color='silver', width=1),
                             mode='lines', name='Presion Red 2', legendgroup="Ref2", showlegend=True),
                  secondary_y=False, row=3, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df2["sp_patomizacion"],
                             line=dict(color='grey', width=1, dash='dash'),
                             mode='lines', name='sp_patomizacion 2', legendgroup="Ref2", showlegend=True),
                  secondary_y=False, row=3, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df2["patomizacion"],
                             line=dict(color='olivedrab', width=1),
                             mode='lines', name='patomizacion 2', legendgroup="Ref2", showlegend=True),
                  secondary_y=False, row=3, col=1)
    # ----------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------
    # SP_PABANICO
    fig.add_trace(go.Scatter(x=df.index, y=df["sp_pabanico"],
                             line=dict(color='darkorange', width=1, dash='dash'),
                             mode='lines', name='sp_pabanico 1', legendgroup="Ref", showlegend=True),
                  secondary_y=False, row=4, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["pabanico"],
                             line=dict(color='steelblue', width=1),
                             mode='lines', name='pabanico 1', legendgroup="Ref", showlegend=True),
                  secondary_y=False, row=4, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["presion_red"],
                             line=dict(color='black', width=1),
                             mode='lines', name='Presion Red 1', legendgroup="Ref", showlegend=False),
                  secondary_y=False, row=4, col=1)
    # ----------------------------------------------------------------------------------------------------------
    fig.add_trace(go.Scatter(x=df.index, y=df2["sp_pabanico"],
                             line=dict(color='grey', width=1, dash='dash'),
                             mode='lines', name='sp_pabanico 2', legendgroup="Ref2", showlegend=True),
                  secondary_y=False, row=4, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df2["pabanico"],
                             line=dict(color='olivedrab', width=1),
                             mode='lines', name='pabanico 2', legendgroup="Ref2", showlegend=True),
                  secondary_y=False, row=4, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df2["presion_red"],
                             line=dict(color='silver', width=1),
                             mode='lines', name='Presion Red 2', legendgroup="Ref2", showlegend=False),
                  secondary_y=False, row=4, col=1)
    # ----------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------
    # Add figure title
    fig.update_layout(height=1000, title=title_plot, legend=dict(orientation="v", ))
    fig.update_layout(modebar_add=["v1hovermode", "toggleSpikeLines"])

    # Template
    fig.layout.template = 'seaborn'  # ggplot2, plotly_dark, seaborn, plotly, plotly_white

    # Set x-axis and y-axis title
    # fig.update_xaxes(title = "xaxis title")
    # fig['layout']['xaxis']['title']='Tiempo'
    fig['layout']['xaxis4']['title'] = 'Fecha'
    fig['layout']['yaxis']['title'] = 'Referencia'
    fig['layout']['yaxis2']['title'] = 'Flujo Masico'
    fig['layout']['yaxis3']['title'] = 'P Atomización'
    fig['layout']['yaxis4']['title'] = 'P Abanico'
    fig.update_xaxes(showline=True, linewidth=0.5, linecolor='black')
    fig.update_yaxes(showline=True, linewidth=0.5, linecolor='black')

    # fig.show())

    return fig
