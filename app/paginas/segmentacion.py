from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# 1. RUTAS DE LOS ARCHIVOS
# ============================================================

# segmentacion.py está dentro de app/paginas/.
# parent.parent permite regresar a la carpeta app/.
APP_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = APP_DIR / "data"

RUTA_ZONAS = DATA_DIR / "zonas_segmentadas.csv"
RUTA_PERFILES = DATA_DIR / "perfiles_horarios.csv"
RUTA_SILUETA = DATA_DIR / "silueta_k.csv"
RUTA_CLUSTERS = DATA_DIR / "resumen_clusters.csv"


# ============================================================
# 2. CARGA DE DATOS
# ============================================================

@st.cache_data
def cargar_datos():
    """
    Carga los archivos precalculados en preparacion.ipynb.

    La segmentación no se vuelve a entrenar dentro de Streamlit;
    la app únicamente consulta y visualiza los resultados.
    """

    zonas = pd.read_csv(RUTA_ZONAS)
    perfiles = pd.read_csv(RUTA_PERFILES)
    silueta = pd.read_csv(RUTA_SILUETA)
    clusters = pd.read_csv(RUTA_CLUSTERS)

    return zonas, perfiles, silueta, clusters


try:
    zonas, perfiles, silueta, clusters = cargar_datos()

except FileNotFoundError as error:
    st.error(
        "No se encontró uno de los archivos necesarios en app/data/."
    )
    st.code(str(error))
    st.stop()

except Exception as error:
    st.error(
        "Ocurrió un error al cargar los datos de segmentación."
    )
    st.exception(error)
    st.stop()


# ============================================================
# 3. ENCABEZADO
# ============================================================

st.title("🗺️ Segmentación de zonas")

st.markdown(
    """
    Esta página agrupa las zonas de taxis de Nueva York según
    **nivel de actividad, características de los viajes y patrones horarios**.

    La segmentación fue calculada previamente con **StandardScaler + K-Means**,
    y PCA se utiliza únicamente para representar los grupos en dos dimensiones.
    """
)


# ============================================================
# 4. RESUMEN GENERAL
# ============================================================

mejor_fila = silueta.loc[
    silueta["silueta"].idxmax()
]

mejor_k = int(mejor_fila["k"])
mejor_silueta = float(mejor_fila["silueta"])

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Zonas segmentadas",
        f"{len(zonas)}",
        border=True,
    )

with col2:
    st.metric(
        "Número de grupos",
        mejor_k,
        border=True,
    )

with col3:
    st.metric(
        "Mejor silueta",
        f"{mejor_silueta:.4f}",
        border=True,
    )


# ============================================================
# 5. DESCRIPCIÓN DE LOS GRUPOS
# ============================================================

st.subheader("Perfiles encontrados")

for _, fila in clusters.sort_values("cluster").iterrows():

    cluster_id = int(fila["cluster"])
    nombre = fila["nombre_grupo"]
    descripcion = fila["descripcion"]

    cantidad = int(
        (zonas["cluster"] == cluster_id).sum()
    )

    with st.container(border=True):
        st.markdown(
            f"#### {nombre}"
        )

        st.caption(
            f"Cluster {cluster_id} · {cantidad} zonas"
        )

        st.write(descripcion)


# ============================================================
# 6. FILTRO DE GRUPOS
# ============================================================

st.subheader("Explorar los grupos")

grupos = (
    zonas["nombre_grupo"]
    .dropna()
    .drop_duplicates()
    .tolist()
)

grupos_seleccionados = st.pills(
    "Grupos visibles",
    grupos,
    selection_mode="multi",
    default=grupos,
)

if not grupos_seleccionados:
    st.warning(
        "Selecciona al menos un grupo para visualizar las zonas."
    )
    st.stop()

zonas_filtradas = zonas[
    zonas["nombre_grupo"].isin(
        grupos_seleccionados
    )
].copy()


# ============================================================
# 7. GRÁFICA PCA INTERACTIVA
# ============================================================

st.subheader("Mapa PCA de las zonas")

st.caption(
    "Cada punto representa una zona. "
    "Puedes seleccionar puntos individualmente, con un recuadro "
    "o con selección libre."
)

fig_pca = px.scatter(
    zonas_filtradas,
    x="pca_1",
    y="pca_2",
    color="nombre_grupo",
    hover_name="zona",
    hover_data={
        "zona_id": True,
        "distrito": True,
        "viajes_dia": ":.1f",
        "distancia_mediana": ":.2f",
        "tarifa_mediana": ":.2f",
        "cluster": False,
        "pca_1": ":.2f",
        "pca_2": ":.2f",
    },
    custom_data=[
        "zona_id",
        "zona",
        "distrito",
    ],
    labels={
        "pca_1": "Componente principal 1",
        "pca_2": "Componente principal 2",
        "nombre_grupo": "Grupo",
    },
)

fig_pca.update_traces(
    marker={
        "size": 10,
        "opacity": 0.8,
    }
)

fig_pca.update_layout(
    legend_title_text="Segmentos",
    hovermode="closest",
)

evento = st.plotly_chart(
    fig_pca,
    use_container_width=True,
    on_select="rerun",
    selection_mode=(
        "points",
        "box",
        "lasso",
    ),
    key="grafico_pca",
)


# ============================================================
# 8. RECUPERAR ZONAS SELECCIONADAS EN EL PCA
# ============================================================

puntos_seleccionados = []

try:
    puntos_seleccionados = evento.selection.points
except Exception:
    puntos_seleccionados = []

ids_seleccionados = []

for punto in puntos_seleccionados:

    customdata = punto.get(
        "customdata",
        []
    )

    if customdata:
        ids_seleccionados.append(
            int(customdata[0])
        )

if ids_seleccionados:

    zonas_detalle = zonas_filtradas[
        zonas_filtradas["zona_id"].isin(
            ids_seleccionados
        )
    ].copy()

    st.success(
        f"{len(zonas_detalle)} zona(s) seleccionada(s) en el gráfico."
    )

else:
    zonas_detalle = zonas_filtradas.copy()


# ============================================================
# 9. DETALLE DE UNA ZONA
# ============================================================

st.subheader("Detalle de zona")

opciones_zonas = (
    zonas_detalle
    .sort_values("zona")
    ["zona"]
    .tolist()
)

zona_elegida = st.selectbox(
    "Selecciona una zona",
    opciones_zonas,
)

fila_zona = zonas_detalle[
    zonas_detalle["zona"] == zona_elegida
].iloc[0]

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "Viajes por día",
        f"{fila_zona['viajes_dia']:.1f}",
        border=True,
    )

with c2:
    st.metric(
        "Distancia mediana",
        f"{fila_zona['distancia_mediana']:.2f} mi",
        border=True,
    )

with c3:
    st.metric(
        "Tarifa mediana",
        f"${fila_zona['tarifa_mediana']:.2f}",
        border=True,
    )

with c4:
    st.metric(
        "Propina mediana",
        f"${fila_zona['propina_mediana']:.2f}",
        border=True,
    )

with st.container(border=True):

    st.markdown(
        f"### {fila_zona['zona']}"
    )

    st.write(
        f"**Distrito:** {fila_zona['distrito']}"
    )

    st.write(
        f"**Grupo:** {fila_zona['nombre_grupo']}"
    )

    st.write(
        fila_zona["descripcion_grupo"]
    )


# ============================================================
# 10. PERFIL HORARIO DE LA ZONA
# ============================================================

st.subheader("Perfil horario")

zona_id = int(
    fila_zona["zona_id"]
)

perfil_zona = perfiles[
    perfiles["zona_id"] == zona_id
].copy()

perfil_zona = perfil_zona.sort_values(
    "hora"
)

fig_horario = px.area(
    perfil_zona,
    x="hora",
    y="proporcion",
    labels={
        "hora": "Hora del día",
        "proporcion": "Proporción de viajes",
    },
)

fig_horario.update_xaxes(
    dtick=1
)

fig_horario.update_layout(
    showlegend=False
)

st.plotly_chart(
    fig_horario,
    use_container_width=True,
)

st.caption(
    "La curva representa qué proporción de los viajes de la zona "
    "ocurre en cada hora del día."
)


# ============================================================
# 11. TABLA DE ZONAS
# ============================================================

st.subheader("Zonas visibles")

tabla = zonas_detalle[
    [
        "zona",
        "distrito",
        "nombre_grupo",
        "viajes_dia",
        "distancia_mediana",
        "tarifa_mediana",
        "pct_fin_semana",
        "pct_manana",
        "pct_tarde",
        "pct_noche",
    ]
].copy()

for columna in [
    "pct_fin_semana",
    "pct_manana",
    "pct_tarde",
    "pct_noche",
]:
    tabla[columna] = (
        tabla[columna] * 100
    )

st.dataframe(
    tabla,
    use_container_width=True,
    hide_index=True,
    column_config={
        "zona": "Zona",
        "distrito": "Distrito",
        "nombre_grupo": "Grupo",

        "viajes_dia": st.column_config.NumberColumn(
            "Viajes/día",
            format="%.1f",
        ),

        "distancia_mediana": st.column_config.NumberColumn(
            "Distancia mediana",
            format="%.2f mi",
        ),

        "tarifa_mediana": st.column_config.NumberColumn(
            "Tarifa mediana",
            format="$%.2f",
        ),

        "pct_fin_semana": st.column_config.NumberColumn(
            "Fin de semana",
            format="%.1f%%",
        ),

        "pct_manana": st.column_config.NumberColumn(
            "Mañana",
            format="%.1f%%",
        ),

        "pct_tarde": st.column_config.NumberColumn(
            "Tarde",
            format="%.1f%%",
        ),

        "pct_noche": st.column_config.NumberColumn(
            "Noche",
            format="%.1f%%",
        ),
    },
)


# ============================================================
# 12. JUSTIFICACIÓN DEL NÚMERO DE CLUSTERS
# ============================================================

with st.expander(
    "¿Por qué se utilizaron cuatro grupos?"
):

    st.write(
        "El número de clusters se seleccionó mediante el "
        "coeficiente de silueta, evaluando valores de k entre 2 y 7."
    )

    fig_silueta = px.line(
        silueta,
        x="k",
        y="silueta",
        markers=True,
        labels={
            "k": "Número de clusters (k)",
            "silueta": "Coeficiente de silueta",
        },
    )

    fig_silueta.update_xaxes(
        dtick=1
    )

    st.plotly_chart(
        fig_silueta,
        use_container_width=True,
    )

    st.info(
        f"El mejor resultado fue k = {mejor_k}, "
        f"con una silueta de {mejor_silueta:.4f}. "
        "Por ello se utilizó ese número de grupos en el modelo final."
    )


# ============================================================
# 13. NOTA METODOLÓGICA
# ============================================================

with st.expander(
    "Metodología utilizada"
):

    st.markdown(
        """
        - Se utilizaron zonas con al menos **500 viajes** en enero.
        - Las variables se estandarizaron con **StandardScaler**.
        - Se evaluó K-Means para valores de **k entre 2 y 7**.
        - El número de grupos se eligió mediante **coeficiente de silueta**.
        - PCA se utilizó para representar los grupos en dos dimensiones.
        - La segmentación se calculó previamente en el notebook y la app
          únicamente carga los resultados.
        """
    )