import streamlit as st


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="Taxis NYC",
    page_icon="🚕",
    layout="wide",
)


# ============================================================
# PÁGINAS
# ============================================================

pagina_pronostico = st.Page(
    "paginas/pronostico.py",
    title="Pronóstico",
    icon="📈",
)

pagina_segmentacion = st.Page(
    "paginas/segmentacion.py",
    title="Segmentación de zonas",
    icon="🗺️",
)

pagina_decision = st.Page(
    "paginas/decision.py",
    title="Decisión",
    icon="🚕",
)


# ============================================================
# NAVEGACIÓN
# ============================================================

navegacion = st.navigation(
    [
        pagina_pronostico,
        pagina_segmentacion,
        pagina_decision,
    ]
)

navegacion.run()