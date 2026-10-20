import numpy as np
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
    API_URL = "http://127.0.0.1:8000"


# ============================================================
# 2. CONSULTAS A LA API
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

    respuesta.raise_for_status()

    return respuesta.json()


# ============================================================
# 3. ENCABEZADO
# ============================================================

st.title(
    "🚕 Decisión de taxis"
)

st.write(
    """
    Define el costo de enviar un taxi de más y el costo de
    perder un pasajero. La aplicación seleccionará el cuantil
    más conveniente para recomendar cuántos taxis enviar.
    """
)


# ============================================================
# 4. OBTENER INFORMACIÓN
# ============================================================

try:

    info = obtener_info()

except requests.RequestException:

    st.error(
        "No fue posible conectar con la API."
    )

    st.stop()


# ============================================================
# 5. ZONA
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
# 6. FECHA
# ============================================================

fechas = info[
    "fechas"
]

# Para mostrar la comparación de costos por defecto,
# seleccionamos el último día con datos reales.
fecha_real_predeterminada = (
    info["periodo"]["fin_prueba"]
)

fecha = st.segmented_control(
    "Fecha",
    fechas,
    default=fecha_real_predeterminada,
)


# ============================================================
# 7. PRONÓSTICO
# ============================================================

try:

    datos = obtener_pronostico(
        zona_id,
        fecha,
    )

except requests.RequestException:

    st.error(
        "No se pudo obtener el pronóstico."
    )

    st.stop()


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
# 8. PANEL DE DECISIÓN
# ============================================================

@st.fragment
def panel_decision(
    datos_dia,
):

    st.subheader(
        "Costos de operación"
    )

    col1, col2 = st.columns(
        2
    )

    with col1:

        costo_ocioso = st.number_input(
            "Costo de un taxi ocioso por hora ($)",
            min_value=1.0,
            value=10.0,
            step=1.0,
        )

    with col2:

        costo_perdido = st.number_input(
            "Costo de un pasajero perdido ($)",
            min_value=1.0,
            value=40.0,
            step=1.0,
        )

    # --------------------------------------------------------
    # CUANTIL ÓPTIMO
    # --------------------------------------------------------

    cuantil_optimo = (
        costo_perdido
        / (
            costo_perdido
            + costo_ocioso
        )
    )

    cuantiles_disponibles = [
        float(q)
        for q in info["cuantiles"]
    ]

    cuantil_utilizado = min(
        cuantiles_disponibles,
        key=lambda q: abs(
            q - cuantil_optimo
        ),
    )

    nombre_cuantil = (
        f"p{int(round(cuantil_utilizado * 100))}"
    )

    st.latex(
        r"q^* = \frac{C_p}{C_p + C_o}"
    )

    c1, c2 = st.columns(
        2
    )

    with c1:

        st.metric(
            "Cuantil óptimo",
            f"{cuantil_optimo:.0%}",
            border=True,
        )

    with c2:

        st.metric(
            "Cuantil utilizado",
            nombre_cuantil,
            border=True,
        )

    st.info(
        f"Con estos costos se utiliza **{nombre_cuantil}**. "
        "Esto significa que la recomendación considera un escenario "
        "más alto cuando perder pasajeros resulta más costoso que "
        "tener taxis sin pasajero."
    )

    # --------------------------------------------------------
    # RECOMENDACIÓN
    # --------------------------------------------------------

    plan = datos_dia.copy()

    plan[
        "taxis_recomendados"
    ] = np.ceil(
        plan[nombre_cuantil]
    ).astype(int)

    plan[
        "taxis_p50"
    ] = np.ceil(
        plan["p50"]
    ).astype(int)

    plan[
        "taxis_semana"
    ] = np.ceil(
        plan["hace_una_semana"]
    ).astype(int)

    st.subheader(
        "Plan recomendado"
    )

    total_taxis = plan[
        "taxis_recomendados"
    ].sum()

    st.metric(
        "Taxis-hora recomendados",
        f"{total_taxis:,}",
        border=True,
    )

    # --------------------------------------------------------
    # GRÁFICA
    # --------------------------------------------------------

    figura = go.Figure()

    figura.add_trace(
        go.Scatter(
            x=plan["hora"],
            y=plan[
                "taxis_recomendados"
            ],
            mode="lines+markers",
            name="Recomendación",
        )
    )

    figura.add_trace(
        go.Scatter(
            x=plan["hora"],
            y=plan["taxis_p50"],
            mode="lines",
            name="Pronóstico p50",
        )
    )

    if plan[
        "real"
    ].notna().any():

        figura.add_trace(
            go.Scatter(
                x=plan["hora"],
                y=plan["real"],
                mode="markers",
                name="Demanda real",
            )
        )

    figura.update_layout(
        xaxis_title="Hora",
        yaxis_title="Taxis / viajes",
        hovermode="x unified",
    )

    figura.update_xaxes(
        dtick=1
    )

    st.plotly_chart(
        figura,
        width="stretch",
    )

    # --------------------------------------------------------
    # COMPARACIÓN DE COSTOS
    # --------------------------------------------------------

    if plan[
        "real"
    ].notna().all():

        real = plan[
            "real"
        ].to_numpy()

        recomendados = plan[
            "taxis_recomendados"
        ].to_numpy()

        central = plan[
            "taxis_p50"
        ].to_numpy()

        semanal = plan[
            "taxis_semana"
        ].to_numpy()

        def calcular_costo(
            enviados,
        ):

            taxis_ociosos = np.maximum(
                enviados - real,
                0,
            )

            pasajeros_perdidos = np.maximum(
                real - enviados,
                0,
            )

            return float(
                np.sum(
                    taxis_ociosos
                    * costo_ocioso
                    + pasajeros_perdidos
                    * costo_perdido
                )
            )

        costo_recomendado = calcular_costo(
            recomendados
        )

        costo_p50 = calcular_costo(
            central
        )

        costo_semana = calcular_costo(
            semanal
        )

        st.subheader(
            "Comparación de costos"
        )

        c1, c2, c3 = st.columns(
            3
        )

        with c1:

            st.metric(
                "Recomendación",
                f"${costo_recomendado:,.0f}",
                border=True,
            )

        with c2:

            st.metric(
                "Pronóstico p50",
                f"${costo_p50:,.0f}",
                delta=(
                    f"${costo_p50 - costo_recomendado:,.0f}"
                ),
                delta_color="inverse",
                border=True,
            )

        with c3:

            st.metric(
                "Hace una semana",
                f"${costo_semana:,.0f}",
                delta=(
                    f"${costo_semana - costo_recomendado:,.0f}"
                ),
                delta_color="inverse",
                border=True,
            )

    else:

        st.info(
            "Esta fecha corresponde al futuro. "
            "El plan puede calcularse, pero todavía no existe "
            "demanda real para comparar sus costos."
        )

    # --------------------------------------------------------
    # TABLA Y DESCARGA
    # --------------------------------------------------------

    tabla_plan = plan[
        [
            "hora",
            nombre_cuantil,
            "taxis_recomendados",
            "p50",
            "hace_una_semana",
            "real",
        ]
    ].copy()

    tabla_plan = tabla_plan.rename(
        columns={
            nombre_cuantil:
                "pronostico_cuantil",
        }
    )

    st.subheader(
        "Plan por hora"
    )

    st.dataframe(
        tabla_plan,
        width="stretch",
        hide_index=True,
    )

    csv = tabla_plan.to_csv(
        index=False
    ).encode(
        "utf-8"
    )

    st.download_button(
        "⬇️ Descargar plan de taxis",
        data=csv,
        file_name=(
            f"plan_taxis_{zona_id}_{fecha}.csv"
        ),
        mime="text/csv",
    )


panel_decision(
    df
)