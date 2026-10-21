import streamlit as st


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="Taxis NYC",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# ESTILO GLOBAL DE LA APLICACIÓN
# ============================================================

st.markdown(
    """
    <style>

    /* ========================================================
       PALETA GLOBAL
       ======================================================== */

    :root {

        /* Fondos */
        --fondo-principal: #F5F7F6;
        --fondo-sidebar: #E8EEF0;
        --fondo-tarjeta: #FFFFFF;

        /* Texto */
        --texto-principal: #26343D;
        --texto-secundario: #66727A;

        /* Bordes */
        --borde-suave: #D6DEE2;

        /* Colores de la temática */
        --amarillo-taxi: #E6C55F;
        --amarillo-pastel: #F5E7AE;

        --verde-petroleo: #6FA9A1;
        --verde-pastel: #DDEBE7;

        --azul-ciudad: #7FA6C3;
        --azul-pastel: #DDEAF2;

        --terracota: #C98F72;
        --terracota-pastel: #F1DDD2;

        --lavanda: #B7A8C9;
        --lavanda-pastel: #E8E1EF;

        /* Sombras */
        --sombra-suave:
            0 2px 10px rgba(38, 52, 61, 0.06);
    }


    /* ========================================================
       APLICACIÓN
       ======================================================== */

    .stApp {
        background-color: var(--fondo-principal);
        color: var(--texto-principal);
    }


    /* Contenedor principal */

    .block-container {
        max-width: 1450px;
        padding-top: 2.5rem;
        padding-bottom: 3rem;
    }


    /* ========================================================
       SIDEBAR
       ======================================================== */

    section[data-testid="stSidebar"] {
        background-color: var(--fondo-sidebar);
        border-right: 1px solid var(--borde-suave);
    }


    section[data-testid="stSidebar"] * {
        color: var(--texto-principal);
    }


    /* Elemento seleccionado de navegación */

    section[data-testid="stSidebar"]
    a[aria-current="page"] {
        background-color: var(--amarillo-pastel);
        border-radius: 9px;
        font-weight: 600;
    }


    /* Hover de navegación */

    section[data-testid="stSidebar"] a:hover {
        background-color: rgba(245, 231, 174, 0.55);
        border-radius: 9px;
    }


    /* ========================================================
       TÍTULOS
       ======================================================== */

    h1 {
        color: var(--texto-principal);
        font-weight: 750;
        letter-spacing: -0.025em;
    }


    h2 {
        color: var(--texto-principal);
        font-weight: 700;
        letter-spacing: -0.015em;
    }


    h3,
    h4 {
        color: var(--texto-principal);
        font-weight: 650;
    }


    /* ========================================================
       TEXTO
       ======================================================== */

    p,
    li,
    label,
    small,
    .stCaption {
        color: var(--texto-secundario);
        line-height: 1.55;
    }


    /* ========================================================
       CONTENEDORES CON BORDE
       ======================================================== */

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: var(--fondo-tarjeta);
        border: 1px solid var(--borde-suave);
        border-radius: 14px;
        box-shadow: var(--sombra-suave);
    }


    /* ========================================================
       MÉTRICAS
       ======================================================== */

    div[data-testid="stMetric"] {
        background-color: var(--fondo-tarjeta);
        border: 1px solid var(--borde-suave);
        border-radius: 14px;
        padding: 14px 16px;
        box-shadow: var(--sombra-suave);
    }


    div[data-testid="stMetricLabel"] {
        color: var(--texto-secundario);
        font-weight: 600;
    }


    div[data-testid="stMetricValue"] {
        color: var(--texto-principal);
        font-weight: 700;
    }


    div[data-testid="stMetricDelta"] {
        font-weight: 600;
    }


    /* ========================================================
       TABS
       ======================================================== */

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: none;
    }


    .stTabs [data-baseweb="tab"] {
        background-color: var(--azul-pastel);
        border: 1px solid var(--borde-suave);
        border-radius: 10px;
        padding: 8px 14px;
        color: var(--texto-principal);
    }


    .stTabs [data-baseweb="tab"]:hover {
        background-color: var(--verde-pastel);
    }


    .stTabs [aria-selected="true"] {
        background-color: var(--amarillo-pastel);
        border-color: var(--amarillo-taxi);
        color: var(--texto-principal);
        font-weight: 600;
    }


    /* ========================================================
       EXPANDERS
       ======================================================== */

    div[data-testid="stExpander"] {
        background-color: var(--fondo-tarjeta);
        border: 1px solid var(--borde-suave);
        border-radius: 12px;
        overflow: hidden;
        box-shadow: var(--sombra-suave);
    }


    /* ========================================================
       BOTONES
       ======================================================== */

    .stButton > button,
    .stDownloadButton > button {

        background-color: var(--azul-pastel);

        color: var(--texto-principal);

        border: 1px solid var(--borde-suave);

        border-radius: 10px;

        min-height: 44px;

        font-weight: 600;

        transition:
            background-color 0.15s ease,
            border-color 0.15s ease,
            transform 0.15s ease;
    }


    .stButton > button:hover,
    .stDownloadButton > button:hover {

        background-color: var(--amarillo-pastel);

        border-color: var(--amarillo-taxi);

        color: var(--texto-principal);
    }


    .stButton > button:active,
    .stDownloadButton > button:active {

        transform: scale(0.98);
    }


    .stButton > button:focus,
    .stDownloadButton > button:focus {

        outline: 2px solid var(--azul-ciudad);

        outline-offset: 2px;
    }


    /* ========================================================
       SELECTBOX
       ======================================================== */

    div[data-baseweb="select"] > div {

        background-color: var(--fondo-tarjeta);

        border-color: var(--borde-suave);

        border-radius: 10px;

        color: var(--texto-principal);
    }


    /* ========================================================
       INPUTS
       ======================================================== */

    div[data-testid="stNumberInput"] input,
    div[data-testid="stTextInput"] input {

        background-color: var(--fondo-tarjeta);

        border-color: var(--borde-suave);

        border-radius: 10px;

        color: var(--texto-principal);
    }


    /* ========================================================
       SEGMENTED CONTROL
       ======================================================== */

    div[data-testid="stSegmentedControl"] {

        border-radius: 10px;
    }


    /* ========================================================
       PILLS
       ======================================================== */

    div[data-testid="stPills"] button {

        border-radius: 20px;

        border: 1px solid var(--borde-suave);

        background-color: var(--azul-pastel);

        color: var(--texto-principal);
    }


    div[data-testid="stPills"] button:hover {

        background-color: var(--verde-pastel);
    }


    /* ========================================================
       ALERTAS
       ======================================================== */

    div[data-baseweb="notification"] {

        border-radius: 12px;

        border: 1px solid var(--borde-suave);
    }


    /* ========================================================
       STATUS
       ======================================================== */

    div[data-testid="stStatusWidget"] {

        border-radius: 12px;

        border-color: var(--borde-suave);
    }


    /* ========================================================
       DATAFRAMES
       ======================================================== */

    div[data-testid="stDataFrame"] {

        background-color: var(--fondo-tarjeta);

        border: 1px solid var(--borde-suave);

        border-radius: 12px;

        overflow: hidden;
    }


    /* ========================================================
       GRÁFICOS PLOTLY
       ======================================================== */

    div[data-testid="stPlotlyChart"] {

        background-color: var(--fondo-tarjeta);

        border: 1px solid var(--borde-suave);

        border-radius: 14px;

        padding: 8px;

        box-shadow: var(--sombra-suave);
    }


    /* ========================================================
       BADGES
       ======================================================== */

    div[data-testid="stBadge"] {

        border-radius: 20px;
    }


    /* ========================================================
       DIVISORES
       ======================================================== */

    hr {

        border-color: var(--borde-suave);

        opacity: 0.8;
    }


    /* ========================================================
       LINKS
       ======================================================== */

    a {

        color: #527D91;

        text-decoration: none;
    }


    a:hover {

        color: #375E70;

        text-decoration: underline;
    }


    /* ========================================================
       TOOLTIP / HELP
       ======================================================== */

    [data-testid="stTooltipIcon"] {

        color: var(--texto-secundario);
    }


    /* ========================================================
       SCROLLBAR
       ======================================================== */

    ::-webkit-scrollbar {

        width: 10px;

        height: 10px;
    }


    ::-webkit-scrollbar-track {

        background: transparent;
    }


    ::-webkit-scrollbar-thumb {

        background: #C7D2D7;

        border-radius: 20px;
    }


    ::-webkit-scrollbar-thumb:hover {

        background: #AEBEC5;
    }


    /* ========================================================
       RESPONSIVE
       ======================================================== */

    @media (max-width: 768px) {

        .block-container {

            padding-left: 1rem;

            padding-right: 1rem;

            padding-top: 1.5rem;
        }


        div[data-testid="stMetric"] {

            padding: 12px;
        }


        h1 {

            font-size: 2rem;
        }

    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# NAVEGACIÓN
# ============================================================

paginas = {

    "Planificar": [

        st.Page(
            "paginas/pronostico.py",
            title="Pronóstico",
            icon=":material/query_stats:",
            default=True,
        ),

        st.Page(
            "paginas/decision.py",
            title="Decisión",
            icon=":material/tune:",
        ),

    ],


    "Entender": [

        st.Page(
            "paginas/segmentacion.py",
            title="Segmentación de zonas",
            icon=":material/hub:",
        ),

        st.Page(
            "paginas/ficha_modelo.py",
            title="Ficha del modelo",
            icon=":material/description:",
        ),

    ],

}


pagina = st.navigation(
    paginas,
    position="sidebar",
    expanded=True,
)


# ============================================================
# INFORMACIÓN DEL PROYECTO
# ============================================================

with st.sidebar:

    st.divider()

    st.markdown(
        "**Taxis NYC**"
    )

    st.caption(
        "Demanda de taxis amarillos de Nueva York."
    )

    st.caption(
        "Datos: enero de 2024 · NYC TLC"
    )

    st.badge(
        "API en línea",
        color="green",
    )


# ============================================================
# EJECUTAR PÁGINA SELECCIONADA
# ============================================================

pagina.run()