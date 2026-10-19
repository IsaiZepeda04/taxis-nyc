import streamlit as st


# ============================================================
# CONFIGURACIÓN GENERAL DE LA APLICACIÓN
# ============================================================

st.set_page_config(
    page_title="Taxis NYC",
    page_icon="🚕",
    layout="wide",
)


# ============================================================
# NAVEGACIÓN
# ============================================================

# En esta etapa solo publicamos la página de segmentación.
# Las demás páginas se agregarán en las siguientes fases.
pagina_segmentacion = st.Page(
    "paginas/segmentacion.py",
    title="Segmentación de zonas",
    icon="🗺️",
)

navegacion = st.navigation(
    [
        pagina_segmentacion,
    ]
)

navegacion.run()