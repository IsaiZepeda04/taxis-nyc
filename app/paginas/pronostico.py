import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st


# ============================================================
# 1. DIRECCIÓN DE LA API
# ============================================================

try:
    API_URL = st.secrets["API_URL"]

except Exception:
    # Se utiliza mientras trabajamos localmente.
    API_URL = "http://127.0.0.1:8000"


# ============================================================
# 2. FUNCIONES PARA CONSULTAR LA API
# ============================================================

@st.cache_data(
    ttl=3600,
    show_spinner=False,
)
def obtener_info():

    respuesta = requests.get(
        f"{API_URL}/info",
        timeout=90,
    )

    respuesta.raise_for_status()

    return respuesta.json()


@st.cache_data(
    ttl=3600,
    show_spinner=False,
)
def obtener_pronostico(
    zona_id,
    fecha,
):

    respuesta = requests.get(
        f"{API_URL}/pronostico",
        params={
            "zona_id": zona_id,
            "fecha": fecha,
        },
        timeout=90,
    )

    if respuesta.status_code == 404:

        detalle = respuesta.json().get(
            "detail",
            "No hay pronóstico disponible.",
        )

        raise ValueError(
            detalle
        )

    respuesta.raise_for_status()

    return respuesta.json()


# ============================================================
# 3. CONEXIÓN INICIAL
# ============================================================

st.title(
    "📈 Pronóstico de demanda"
)

st.write(
    """
    Consulta la cantidad esperada de viajes por hora y el
    rango de incertidumbre del modelo.
    """
)

try:

    with st.status(
        "Conectando con la API...",
        expanded=False,
    ) as estado:

        info = obtener_info()

        estado.update(
            label="API conectada",
            state="complete",
        )

except requests.RequestException:

    st.error(
        "No fue posible conectar con la API. "
        "Si está publicada en Render, puede tardar unos segundos en despertar."
    )

    st.stop()


# ============================================================
# 4. SELECTOR DE ZONA
# ============================================================

zonas = info["zonas"]

opciones_zonas = {
    f"{zona['nombre']} — {zona['distrito']}":
        zona["id"]
    for zona in zonas
}

nombre_zona = st.selectbox(
    "Zona",
    opciones_zonas.keys(),
)

zona_id = opciones_zonas[
    nombre_zona
]


# ============================================================
# 5. SELECTOR DE FECHA
# ============================================================

fechas = info["fechas"]

fecha_predeterminada = info[
    "periodo"
]["fecha_futura"]

indice_fecha = (
    fechas.index(fecha_predeterminada)
    if fecha_predeterminada in fechas
    else len(fechas) - 1
)

fecha = st.segmented_control(
    "Fecha",
    fechas,
    default=fechas[
        indice_fecha
    ],
)


# ============================================================
# 6. CONSULTAR EL PRONÓSTICO
# ============================================================

try:

    datos = obtener_pronostico(
        zona_id,
        fecha,
    )

except ValueError as error:

    st.warning(
        str(error)
    )

    st.stop()

except requests.RequestException:

    st.error(
        "La API no respondió correctamente."
    )

    st.stop()


# ============================================================
# 7. CONVERTIR RESPUESTA A DATAFRAME
# ============================================================

filas = []

for elemento in datos["horas"]:

    fila = {
        "hora": elemento["hora"],
        "real": elemento["real"],
        "hace_una_semana": elemento[
            "hace_una_semana"
        ],
    }

    fila.update(
        elemento["cuantiles"]
    )

    filas.append(
        fila
    )

df = pd.DataFrame(
    filas
)


# ============================================================
# 8. RESUMEN DEL DÍA
# ============================================================

st.subheader(
    datos["zona"]["nombre"]
)

st.caption(
    f"{datos['zona']['distrito']} · {datos['fecha']}"
)

p50_total = df[
    "p50"
].sum()

p10_total = df[
    "p10"
].sum()

p90_total = df[
    "p90"
].sum()

real_disponible = (
    df["real"]
    .notna()
    .any()
)

col1, col2, col3 = st.columns(
    3
)

with col1:

    st.metric(
        "Pronóstico central",
        f"{p50_total:,.0f} viajes",
        border=True,
    )

with col2:

    st.metric(
        "Escenario bajo p10",
        f"{p10_total:,.0f}",
        border=True,
    )

with col3:

    st.metric(
        "Escenario alto p90",
        f"{p90_total:,.0f}",
        border=True,
    )

if not real_disponible:

    st.info(
        "Esta fecha corresponde al pronóstico futuro. "
        "Todavía no existen valores reales de demanda."
    )


# ============================================================
# 9. GRÁFICA DE PRONÓSTICO
# ============================================================

st.subheader(
    "Pronóstico por hora"
)

figura = go.Figure()

# Límite superior.
figura.add_trace(
    go.Scatter(
        x=df["hora"],
        y=df["p90"],
        mode="lines",
        line=dict(
            width=0,
        ),
        name="p90",
        showlegend=False,
    )
)

# Límite inferior y relleno.
figura.add_trace(
    go.Scatter(
        x=df["hora"],
        y=df["p10"],
        mode="lines",
        fill="tonexty",
        line=dict(
            width=0,
        ),
        name="Intervalo p10-p90",
    )
)

# Pronóstico central.
figura.add_trace(
    go.Scatter(
        x=df["hora"],
        y=df["p50"],
        mode="lines+markers",
        name="Pronóstico p50",
    )
)

# Regla semanal.
figura.add_trace(
    go.Scatter(
        x=df["hora"],
        y=df["hace_una_semana"],
        mode="lines",
        name="Hace una semana",
    )
)

# Valores reales únicamente cuando existen.
if real_disponible:

    figura.add_trace(
        go.Scatter(
            x=df["hora"],
            y=df["real"],
            mode="markers",
            name="Real",
            marker=dict(
                size=8,
            ),
        )
    )

figura.update_layout(
    xaxis_title="Hora del día",
    yaxis_title="Viajes",
    hovermode="x unified",
)

figura.update_xaxes(
    dtick=1
)

st.plotly_chart(
    figura,
    width="stretch",
)


# ============================================================
# 10. TABLA HORARIA
# ============================================================

st.subheader(
    "Detalle por hora"
)

columnas_tabla = [
    "hora",
    "p10",
    "p50",
    "p90",
    "hace_una_semana",
]

if real_disponible:

    columnas_tabla.append(
        "real"
    )

tabla = df[
    columnas_tabla
].copy()

st.dataframe(
    tabla,
    width="stretch",
    hide_index=True,
    column_config={
        "hora": "Hora",
        "p10": st.column_config.NumberColumn(
            "p10",
            format="%.1f",
        ),
        "p50": st.column_config.ProgressColumn(
            "p50",
            format="%.1f",
            min_value=0,
            max_value=float(
                df["p90"].max()
            ),
        ),
        "p90": st.column_config.NumberColumn(
            "p90",
            format="%.1f",
        ),
        "hace_una_semana":
            "Hace una semana",
        "real": "Real",
    },
)