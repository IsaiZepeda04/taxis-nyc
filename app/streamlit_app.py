import streamlit as st

st.set_page_config(
    page_title="Taxis NYC",
    page_icon="🚕",
    layout="wide"
)

paginas = [
    st.Page(
        "paginas/pronostico.py",
        title="Pronóstico",
        icon="📈",
        default=True
    ),
    st.Page(
        "paginas/segmentacion.py",
        title="Segmentación de zonas",
        icon="🗺️"
    ),
    st.Page(
        "paginas/decision.py",
        title="Decisión",
        icon="🚕"
    )
]

pagina = st.navigation(paginas)
pagina.run()